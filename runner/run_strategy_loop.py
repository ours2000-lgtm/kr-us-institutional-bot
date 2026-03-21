# path: runner/run_strategy_loop.py

import os
import sys
from logging import INFO, basicConfig, getLogger

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from broker.kiwoom_adapter import KiwoomAdapter
from broker.kiwoom_broker_snapshot_adapter import KiwoomBrokerSnapshotAdapter
from broker.kiwoom_real_router import KiwoomRealRouter
from core.engine.order_factory import OrderFactory
from core.engine.strategy_engine.strategy_engine import StrategyEngine
from core.execution.execution_controller import ExecutionController
from engine.reconciliation_engine import ReconciliationEngine
from engine.risk_manager import RiskManager
from engine.runtime_reconciliation import RuntimeReconciliationRunner
from core.strategy.test_strategy import TestStrategy


logger = getLogger(__name__)

basicConfig(level=INFO)


def main():
    account_type = os.getenv("ACCOUNT_TYPE", "paper").lower().strip()

    # ---------------------------------
    # ACCOUNT_NO (required)
    # ---------------------------------
    account_no = os.getenv("ACCOUNT_NO", "").strip()
    if not account_no:
        raise ValueError("ACCOUNT_NO environment variable is required")

    logger.info("SYSTEM_START account_type=%s", account_type)
    logger.info("RUN_STRATEGY_LOOP_START")

    # ---------------------------------
    # Adapter & Router
    # ---------------------------------
    adapter = KiwoomAdapter()
    real_router = KiwoomRealRouter()

    symbol = "005930"
    adapter.real_router = real_router
    adapter.default_symbol = symbol

    logger.info("ADAPTER_AND_REAL_ROUTER_CONNECTED symbol=%s", symbol)

    # ---------------------------------
    # Strategy
    # ---------------------------------
    strategy = TestStrategy()
    logger.info("STRATEGY_INITIALIZED class=%s", strategy.__class__.__name__)

    order_factory = OrderFactory()

    risk_manager = RiskManager(
        position_manager=adapter.position_manager,
    )

    adapter.risk_manager = risk_manager

    execution_controller = ExecutionController(
        adapter=adapter,
        order_factory=order_factory,
        risk_manager=risk_manager,
        account_type=account_type,
    )

    # ---------------------------------
    # Critical back-reference wiring
    # ---------------------------------
    adapter.execution_controller = execution_controller

    logger.info(
        "EXECUTION_COMPONENTS_READY order_factory=%s risk_manager=%s position_manager=%s execution_controller=%s",
        order_factory.__class__.__name__,
        risk_manager.__class__.__name__,
        adapter.position_manager.__class__.__name__,
        execution_controller.__class__.__name__,
    )

    engine = StrategyEngine(execution_controller, strategy)
    logger.info("STRATEGY_ENGINE_INITIALIZED class=%s", engine.__class__.__name__)

    # ---------------------------------
    # Reconciliation wiring (before login)
    # ---------------------------------
    broker_snapshot_adapter = KiwoomBrokerSnapshotAdapter(
        kiwoom_adapter=adapter,
        account_no=account_no,
    )

    reconciliation_engine = ReconciliationEngine()

    reconciliation_runner = RuntimeReconciliationRunner(
        reconciliation_engine=reconciliation_engine,
        broker_snapshot_supplier=broker_snapshot_adapter.fetch_snapshot,
    )

    adapter.reconciliation_runner = reconciliation_runner
    adapter.reconciliation_exchange = "KRX"
    adapter.reconciliation_currency = "KRW"
    adapter.reconciliation_instrument_type = "EQUITY"

    logger.info(
        "RECONCILIATION_COMPONENTS_READY broker_snapshot_adapter=%s reconciliation_engine=%s runner=%s",
        broker_snapshot_adapter.__class__.__name__,
        reconciliation_engine.__class__.__name__,
        reconciliation_runner.__class__.__name__,
    )

    # ---------------------------------
    # Tick handler
    # ---------------------------------
    real_router.register_tick_handler(engine.on_tick)
    logger.info("TICK_HANDLER_REGISTERED")

    # ---------------------------------
    # Login
    # ---------------------------------
    adapter.login()
    logger.info("LOGIN_REQUESTED")

    # ---------------------------------
    # Qt loop
    # ---------------------------------
    logger.info("QT_EVENT_LOOP_START")
    adapter.app.exec_()


if __name__ == "__main__":
    main()