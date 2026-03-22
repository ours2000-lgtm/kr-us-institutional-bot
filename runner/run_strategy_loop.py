import os
import sys
import threading
from logging import basicConfig, INFO, getLogger

# -------------------------------------------------
# 프로젝트 루트 Python path 추가
# -------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# Imports
# -------------------------------------------------

from broker.kiwoom_adapter import KiwoomAdapter
from broker.kiwoom_real_router import KiwoomRealRouter
from broker.kiwoom_broker_snapshot_adapter import KiwoomBrokerSnapshotAdapter
from broker.order_event_bridge import OrderEventBridge

from core.engine.order_factory import OrderFactory
from core.engine.strategy_engine.strategy_engine import StrategyEngine
from core.execution.execution_controller import ExecutionController
from core.execution.order_lifecycle import OrderLifecycleManager
from core.execution.order_watchdog import OrderWatchdog

from core.strategy.test_strategy import TestStrategy

from engine.reconciliation_engine import ReconciliationEngine
from engine.runtime_reconciliation import RuntimeReconciliationRunner
from engine.risk_manager import RiskManager
from engine.symbol_cooldown_manager import SymbolCooldownManager

# ---------------------------------------------
# optional evidence writer
# ---------------------------------------------
try:
    from runtime.evidence.control_plane.control_plane_evidence_writer import (
        ControlPlaneEvidenceWriter,
    )
except Exception:
    ControlPlaneEvidenceWriter = None


logger = getLogger(__name__)
basicConfig(level=INFO)


# =================================================
# helpers
# =================================================


def _build_evidence_writer():
    if ControlPlaneEvidenceWriter is None:
        logger.warning("EVIDENCE_WRITER_UNAVAILABLE")
        return None

    try:
        writer = ControlPlaneEvidenceWriter(
            base_dir="runtime/evidence/control_plane"
        )
        logger.info("EVIDENCE_WRITER_READY")
        return writer
    except Exception:
        logger.exception("EVIDENCE_WRITER_INIT_FAILED")
        return None


def _attach_evidence_writer(target, writer, log_msg):
    if target is None or writer is None:
        return

    setter = getattr(target, "set_evidence_writer", None)
    if callable(setter):
        setter(writer)
        logger.info(log_msg)
        return

    try:
        setattr(target, "evidence_writer", writer)
        logger.info(log_msg)
    except Exception:
        logger.exception("%s_FAILED", log_msg)


def _attach_recovery_state_supplier(position_manager, supplier):
    if position_manager is None or supplier is None:
        return

    setter = getattr(position_manager, "set_recovery_state_supplier", None)
    if callable(setter):
        setter(supplier)
        logger.info("POSITION_MANAGER_RECOVERY_SUPPLIER_ATTACHED")
        return

    try:
        position_manager.recovery_state_supplier = supplier
        logger.info("POSITION_MANAGER_RECOVERY_SUPPLIER_ATTACHED")
    except Exception:
        logger.exception("POSITION_MANAGER_RECOVERY_SUPPLIER_ATTACH_FAILED")


def _set_snapshot_adapter_account_no(snapshot_adapter, account_no: str):
    if snapshot_adapter is None or not account_no:
        return

    try:
        snapshot_adapter.account_no = str(account_no).strip()
        logger.info("SNAPSHOT_ACCOUNT_SET account_no=%s", account_no)
    except Exception:
        logger.exception("SNAPSHOT_ACCOUNT_SET_FAILED")


def _start_watchdog_thread(lifecycle, risk, evidence, timeout, interval):
    watchdog = OrderWatchdog(
        lifecycle_manager=lifecycle,
        risk_manager=risk,
        evidence_writer=evidence,
        ack_timeout_sec=timeout,
        check_interval_sec=interval,
    )

    thread = threading.Thread(
        target=watchdog.start,
        name="order-watchdog",
        daemon=True,
    )
    thread.start()

    logger.info(
        "WATCHDOG_STARTED timeout=%s interval=%s",
        timeout,
        interval,
    )

    return watchdog, thread


# =================================================
# main
# =================================================


def main():
    account_type = os.getenv("ACCOUNT_TYPE", "paper").lower().strip()
    account_no = os.getenv("ACCOUNT_NO", "").strip()
    default_symbol = os.getenv("DEFAULT_SYMBOL", "005930").strip()

    ack_timeout = int(os.getenv("ORDER_ACK_TIMEOUT_SEC", "5"))
    interval = int(os.getenv("ORDER_WATCHDOG_CHECK_INTERVAL_SEC", "1"))

    cooldown_minutes = int(os.getenv("SYMBOL_COOLDOWN_MINUTES", "30"))
    ban_on_stop = os.getenv("SYMBOL_BAN_ON_STOP", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }

    logger.info(
        "SYSTEM_START account_type=%s symbol=%s account_set=%s ack_timeout=%s watchdog_interval=%s cooldown_minutes=%s ban_on_stop=%s",
        account_type,
        default_symbol,
        bool(account_no),
        ack_timeout,
        interval,
        cooldown_minutes,
        ban_on_stop,
    )

    # ---------------------------------
    # adapter / router
    # ---------------------------------

    adapter = KiwoomAdapter()
    real_router = KiwoomRealRouter()

    adapter.real_router = real_router
    adapter.default_symbol = default_symbol

    logger.info("ADAPTER_AND_ROUTER_READY")

    # ---------------------------------
    # evidence
    # ---------------------------------

    evidence_writer = _build_evidence_writer()
    adapter.evidence_writer = evidence_writer

    recovery_fsm = getattr(adapter, "recovery_fsm", None)
    position_manager = getattr(adapter, "position_manager", None)

    _attach_evidence_writer(
        recovery_fsm,
        evidence_writer,
        "RECOVERY_FSM_EVIDENCE_ATTACHED",
    )

    _attach_evidence_writer(
        position_manager,
        evidence_writer,
        "POSITION_MANAGER_EVIDENCE_ATTACHED",
    )

    supplier = getattr(recovery_fsm, "get_state", None) if recovery_fsm else None
    _attach_recovery_state_supplier(position_manager, supplier)

    # ---------------------------------
    # reconciliation
    # ---------------------------------

    snapshot_adapter = KiwoomBrokerSnapshotAdapter(
        kiwoom_adapter=adapter,
        account_no=account_no or "0000000000",
    )

    _set_snapshot_adapter_account_no(snapshot_adapter, account_no)

    reconciliation_engine = ReconciliationEngine()
    reconciliation_runner = RuntimeReconciliationRunner(
        reconciliation_engine=reconciliation_engine,
        broker_snapshot_supplier=snapshot_adapter.fetch_snapshot,
    )

    adapter.reconciliation_runner = reconciliation_runner

    logger.info("RECONCILIATION_READY")

    # ---------------------------------
    # risk
    # ---------------------------------

    risk_manager = RiskManager(
        position_manager=adapter.position_manager
    )
    adapter.risk_manager = risk_manager

    logger.info("RISK_MANAGER_READY")

    # ---------------------------------
    # lifecycle / bridge
    # ---------------------------------

    lifecycle = OrderLifecycleManager(evidence_writer=evidence_writer)

    bridge = OrderEventBridge(
        order_lifecycle_manager=lifecycle,
        evidence_writer=evidence_writer,
    )

    adapter.order_event_bridge = bridge

    logger.info("LIFECYCLE_AND_BRIDGE_READY")

    # ---------------------------------
    # cooldown
    # ---------------------------------

    cooldown_manager = SymbolCooldownManager(
        cooldown_minutes=cooldown_minutes,
        ban_on_stop=ban_on_stop,
    )

    logger.info("SYMBOL_COOLDOWN_MANAGER_READY")

    # ---------------------------------
    # watchdog
    # ---------------------------------

    watchdog, _ = _start_watchdog_thread(
        lifecycle,
        risk_manager,
        evidence_writer,
        ack_timeout,
        interval,
    )

    # ---------------------------------
    # execution
    # ---------------------------------

    order_factory = OrderFactory()

    execution_controller = ExecutionController(
        adapter=adapter,
        order_factory=order_factory,
        risk_manager=risk_manager,
        account_type=account_type,
        recovery_state_supplier=supplier,
        evidence_writer=evidence_writer,
        order_lifecycle_manager=lifecycle,
        cooldown_manager=cooldown_manager,
    )

    adapter.execution_controller = execution_controller

    logger.info("EXECUTION_READY")

    # ---------------------------------
    # strategy
    # ---------------------------------

    strategy = TestStrategy()
    engine = StrategyEngine(execution_controller, strategy)

    real_router.register_tick_handler(engine.on_tick)

    logger.info("STRATEGY_ENGINE_READY")

    # ---------------------------------
    # login
    # ---------------------------------

    adapter.login()

    try:
        logger.info("QT_EVENT_LOOP_START")
        adapter.app.exec_()
    finally:
        try:
            watchdog.stop()
        except Exception:
            logger.exception("WATCHDOG_STOP_FAILED")


if __name__ == "__main__":
    main()