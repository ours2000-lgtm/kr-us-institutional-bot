import sys
from logging import getLogger

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtWidgets import QApplication

from broker.fill_normalizer import FillNormalizer
from broker.kiwoom_chejan_parser import KiwoomChejanParser
from core.execution.broker_order_guard import BrokerOrderGuard
from engine.fill_event_store import FillEventStore
from engine.position_manager import PositionManager
from engine.recovery_fsm import (
    RecoveryFSM,
    STATE_BLOCKED,
    STATE_DISCONNECTED,
    STATE_EXIT_ONLY,
    STATE_READY,
    STATE_READY_PENDING,
    STATE_RECOVERING,
    EVENT_COOLDOWN_ELAPSED,
    EVENT_CRITICAL_ERROR,
    EVENT_DISCONNECT_DETECTED,
    EVENT_LOGIN_SUCCESS,
    EVENT_MISMATCH_CRITICAL,
    EVENT_RECONNECT_START,
    EVENT_SNAPSHOT_OK,
)


logger = getLogger(__name__)


class KiwoomAdapter:
    def __init__(self):
        # ----------------------------------
        # Qt Application
        # ----------------------------------
        self.app = QApplication.instance() or QApplication(sys.argv)

        # ----------------------------------
        # Kiwoom OpenAPI
        # ----------------------------------
        self.ocx = QAxWidget()
        self.ocx.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        if self.ocx.isNull():
            raise RuntimeError(
                "KHOpenAPI control load failed. "
                "Check OpenAPI installation and use 32-bit Python."
            )

        # ----------------------------------
        # Internal modules
        # ----------------------------------
        self.chejan_parser = KiwoomChejanParser()
        self.fill_normalizer = FillNormalizer(
            on_error=self._on_fill_normalize_error
        )

        self.fill_store = FillEventStore(
            base_dir="data/fills",
            durability_mode="flush",
            store_raw_event=True,
        )

        self.position_manager = PositionManager(
            on_error=self._on_position_error
        )

        self.order_guard = BrokerOrderGuard()

        # ----------------------------------
        # External shared modules
        # ----------------------------------
        self.risk_manager = None
        self.reconciliation_runner = None
        self.execution_controller = None
        self.evidence_writer = None
        self.order_event_bridge = None

        # reconciliation metadata
        self.reconciliation_exchange = "KRX"
        self.reconciliation_currency = "KRW"
        self.reconciliation_instrument_type = "EQUITY"

        # ----------------------------------
        # Runtime state
        # ----------------------------------
        self.account = None
        self.real_router = None
        self.default_symbol = None

        # intent_id -> {"symbol": ..., "side": ..., "order": ...}
        self._pending_intents = {}

        # ----------------------------------
        # Recovery FSM
        # ----------------------------------
        self.recovery_fsm = RecoveryFSM(
            initial_state=STATE_DISCONNECTED
        )

        # reconnect controls
        self._reconnect_attempts = 0
        self._reconnect_max_attempts = 3
        self._reconnect_backoff_ms = 3000

        self._reconnect_timer = QTimer()
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)

        # READY_PENDING cooldown timer
        self._ready_pending_cooldown_timer = QTimer()
        self._ready_pending_cooldown_timer.setSingleShot(True)
        self._ready_pending_cooldown_timer.timeout.connect(
            self._complete_ready_pending
        )
        self._ready_pending_cooldown_ms = 5000

        # ----------------------------------
        # TR state
        # ----------------------------------
        self.tr_event_loop = None
        self._tr_error = None

        self._account_positions_rows = []
        self._account_positions_next = "0"
        self._account_positions_rqname = "ACCOUNT_POSITIONS_REQ"

        # ----------------------------------
        # Event bindings
        # ----------------------------------
        self.ocx.OnEventConnect.connect(self._on_login)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real)

    # ----------------------------------
    # recovery state compatibility
    # ----------------------------------

    @property
    def recovery_state(self):
        return self.recovery_fsm.get_state()

    # ----------------------------------
    # Login / Recovery
    # ----------------------------------

    def login(self):
        logger.info("LOGIN_REQUESTED")

        if self.recovery_state == STATE_DISCONNECTED:
            self._transition_fsm(
                "RECONNECTING",
                EVENT_RECONNECT_START,
                reason="login_requested",
                allow_noop=True,
            )

        self.ocx.dynamicCall("CommConnect()")

    def _on_login(self, err_code):
        if err_code != 0:
            logger.error("LOGIN_FAILED err_code=%s", err_code)
            self._enter_blocked_state("LOGIN_FAILED")
            return

        accounts = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        account_list = [x for x in accounts.split(";") if x]

        if not account_list:
            logger.error("NO_ACCOUNT_FOUND")
            self._enter_blocked_state("ACCOUNT_LIST_EMPTY")
            return

        self.account = account_list[0]
        logger.info("LOGIN_SUCCESS account=%s", self.account)

        self._stop_reconnect_timer()

        if self.recovery_state == STATE_BLOCKED:
            logger.error(
                "LOGIN_SUCCESS_IGNORED_WHILE_BLOCKED account=%s",
                self.account,
            )
            return

        if self.recovery_state == STATE_DISCONNECTED:
            self._transition_fsm(
                "RECONNECTING",
                EVENT_RECONNECT_START,
                reason="login_success_pre_alignment",
                allow_noop=True,
            )

        self._transition_fsm(
            STATE_RECOVERING,
            EVENT_LOGIN_SUCCESS,
            reason="login_success",
        )

        if not self._restore_realtime_subscription():
            logger.error("REALTIME_RESUBSCRIBE_FAILED")
            self._enter_blocked_state("REALTIME_RESUBSCRIBE_FAILED")
            return

        logger.info(
            "REALTIME_RESUBSCRIBE_COMPLETED symbol=%s",
            self.default_symbol,
        )

        self._start_recovery_validation()

    def _handle_disconnect(self, reason: str):
        if self.recovery_state == STATE_BLOCKED:
            logger.warning(
                "BROKER_DISCONNECTED_IGNORED state=%s reason=%s",
                self.recovery_state,
                reason,
            )
            return

        logger.error("BROKER_DISCONNECTED_DETECTED reason=%s", reason)

        self._stop_ready_pending_cooldown_timer()

        if self.recovery_state in {
            STATE_READY,
            STATE_EXIT_ONLY,
            STATE_READY_PENDING,
            STATE_RECOVERING,
        }:
            self._transition_fsm(
                STATE_DISCONNECTED,
                EVENT_DISCONNECT_DETECTED,
                reason=reason,
                allow_noop=True,
            )

        if self.risk_manager is not None:
            self.risk_manager.block_trading("BROKER_DISCONNECTED")

        self._schedule_reconnect_attempt(event="BROKER_DISCONNECTED")

    def _schedule_reconnect_attempt(self, event: str):
        if self.recovery_state == STATE_BLOCKED:
            logger.error(
                "RECONNECT_SCHEDULE_SKIPPED state=%s event=%s",
                self.recovery_state,
                event,
            )
            return

        if self._reconnect_attempts >= self._reconnect_max_attempts:
            logger.error(
                "RECONNECT_MAX_RETRY_EXCEEDED attempts=%s max_attempts=%s",
                self._reconnect_attempts,
                self._reconnect_max_attempts,
            )
            self._enter_blocked_state("RECONNECT_FAILED")
            return

        if self.recovery_state == STATE_DISCONNECTED:
            self._transition_fsm(
                "RECONNECTING",
                EVENT_RECONNECT_START,
                reason=event,
                allow_noop=True,
            )

        if self._reconnect_timer.isActive():
            logger.info(
                "RECONNECT_TIMER_ALREADY_ACTIVE attempts=%s next_in_ms=%s",
                self._reconnect_attempts,
                self._reconnect_backoff_ms,
            )
            return

        self._stop_ready_pending_cooldown_timer()
        self._reconnect_timer.start(self._reconnect_backoff_ms)

        logger.info(
            "RECONNECT_ATTEMPT_SCHEDULED next_attempt=%s delay_ms=%s",
            self._reconnect_attempts + 1,
            self._reconnect_backoff_ms,
        )

    def _attempt_reconnect(self):
        if self.recovery_state == STATE_BLOCKED:
            logger.error("RECONNECT_ATTEMPT_SKIPPED state=BLOCKED")
            return

        if self._reconnect_attempts >= self._reconnect_max_attempts:
            logger.error(
                "RECONNECT_MAX_RETRY_EXCEEDED attempts=%s max_attempts=%s",
                self._reconnect_attempts,
                self._reconnect_max_attempts,
            )
            self._enter_blocked_state("RECONNECT_FAILED")
            return

        self._reconnect_attempts += 1

        if self.recovery_state == STATE_DISCONNECTED:
            self._transition_fsm(
                "RECONNECTING",
                EVENT_RECONNECT_START,
                reason="timer_reconnect_attempt",
                allow_noop=True,
            )

        logger.info(
            "RECONNECT_ATTEMPT_STARTED attempt=%s max_attempts=%s",
            self._reconnect_attempts,
            self._reconnect_max_attempts,
        )

        self.login()

    def _restore_realtime_subscription(self) -> bool:
        if not self.real_router:
            logger.error("REALTIME_RESUBSCRIBE_FAILED reason=REAL_ROUTER_MISSING")
            return False

        if not self.default_symbol:
            logger.error("REALTIME_RESUBSCRIBE_FAILED reason=DEFAULT_SYMBOL_MISSING")
            return False

        try:
            ret = self.real_router.subscribe_symbol(self, self.default_symbol)
            if ret != 0:
                logger.error("REALTIME_RESUBSCRIBE_FAILED ret=%s", ret)
                return False
            return True
        except Exception:
            logger.exception("REALTIME_RESUBSCRIBE_FAILED")
            return False

    def _start_recovery_validation(self):
        logger.info("RECOVERY_RECONCILIATION_STARTED account=%s", self.account)

        if self.reconciliation_runner is None:
            logger.error("RECOVERY_FAILED reason=RECONCILIATION_RUNNER_MISSING")
            self._enter_blocked_state("RECOVERY_RECONCILIATION_RUNNER_MISSING")
            return

        if self.position_manager is None:
            logger.error("RECOVERY_FAILED reason=POSITION_MANAGER_MISSING")
            self._enter_blocked_state("RECOVERY_POSITION_MANAGER_MISSING")
            return

        if not self.account:
            logger.error("RECOVERY_FAILED reason=ACCOUNT_NOT_READY")
            self._enter_blocked_state("RECOVERY_ACCOUNT_NOT_READY")
            return

        if self.recovery_state != STATE_RECOVERING:
            logger.error(
                "RECOVERY_VALIDATION_INVALID_STATE state=%s",
                self.recovery_state,
            )
            self._enter_blocked_state("RECOVERY_VALIDATION_INVALID_STATE")
            return

        try:
            broker_snapshot_supplier = getattr(
                self.reconciliation_runner,
                "broker_snapshot_supplier",
                None,
            )
            if broker_snapshot_supplier is None:
                raise ValueError("reconciliation_runner missing broker_snapshot_supplier")

            broker_snapshot = broker_snapshot_supplier()

            if not isinstance(broker_snapshot, dict):
                raise ValueError("broker_snapshot must be dict")

            logger.info(
                "RECOVERY_BROKER_SNAPSHOT_FETCHED positions=%s",
                len(broker_snapshot.get("positions", {})),
            )

            replace_fn = getattr(
                self.position_manager,
                "replace_active_positions_from_broker_snapshot",
                None,
            )
            if not callable(replace_fn):
                raise ValueError(
                    "position_manager missing replace_active_positions_from_broker_snapshot"
                )

            replace_result = replace_fn(broker_snapshot)

            logger.warning(
                "RECOVERY_POSITION_SEED_COMPLETED old_active=%s new_active=%s symbols=%s",
                replace_result.get("old_active_count"),
                replace_result.get("new_active_count"),
                replace_result.get("symbols"),
            )

            engine_snapshot = (
                self.position_manager.list_active_position_snapshots_for_reconciliation(
                    account_no=self.account,
                    exchange=self.reconciliation_exchange,
                    currency=self.reconciliation_currency,
                    instrument_type=self.reconciliation_instrument_type,
                )
            )

            recon_outcome = self.reconciliation_runner.run(engine_snapshot)

            should_block = bool(recon_outcome.get("should_block_trading", False))
            block_reason = recon_outcome.get("block_reason")
            result = recon_outcome.get("result")

            if self.risk_manager is not None:
                self.risk_manager.on_reconciliation_result(
                    result=result,
                    should_block_trading=should_block,
                    block_reason=block_reason,
                )

            if should_block:
                logger.error(
                    "RECOVERY_RECONCILIATION_MISMATCH block_reason=%s",
                    block_reason,
                )
                self._enter_blocked_state(
                    block_reason or "RECONCILIATION_DRIFT",
                    event=EVENT_MISMATCH_CRITICAL,
                )
                return

            logger.info("RECOVERY_RECONCILIATION_MATCH")

            if self.risk_manager is not None:
                block_state = self.risk_manager.get_block_state()
                if block_state.get("trading_blocked"):
                    existing_reason = block_state.get("block_reason")
                    if existing_reason == "BROKER_DISCONNECTED":
                        self.risk_manager.clear_block("RECOVERY_MATCHED")
                    else:
                        logger.error(
                            "RECOVERY_MATCH_BUT_OTHER_BLOCK_REMAINS existing_block_reason=%s",
                            existing_reason,
                        )
                        self._enter_blocked_state(existing_reason or "BLOCKED")
                        return

            self._reconnect_attempts = 0

            self._transition_fsm(
                STATE_READY_PENDING,
                EVENT_SNAPSHOT_OK,
                reason="recovery_reconciliation_match",
            )
            self._start_ready_pending_cooldown_timer()

        except Exception:
            logger.exception("RECOVERY_FAILED")
            self._enter_blocked_state("RECOVERY_FAILED")

    def manual_unblock(self):
        """
        BLOCKED -> DISCONNECTED 수동 해제.

        현재 RecoveryFSM은 BLOCKED를 terminal state로 두므로,
        수동 해제 시 FSM 인스턴스를 재생성한 뒤 DISCONNECTED 상태로 복귀시킨다.
        """
        self._stop_reconnect_timer()
        self._stop_ready_pending_cooldown_timer()

        old_fsm = self.recovery_fsm

        new_fsm = RecoveryFSM(initial_state=STATE_DISCONNECTED)
        new_fsm.evidence_writer = self.evidence_writer
        self.recovery_fsm = new_fsm

        if self.position_manager is not None:
            self.position_manager.set_recovery_state_supplier(
                self.recovery_fsm.get_state
            )

        if self.risk_manager is not None:
            self.risk_manager.clear_block("MANUAL_UNBLOCK")

        logger.warning(
            "RECOVERY_MANUAL_UNBLOCKED old_state=%s new_state=%s",
            old_fsm.get_state(),
            self.recovery_state,
        )

    def _complete_ready_pending(self):
        if self.recovery_state != STATE_READY_PENDING:
            self._stop_ready_pending_cooldown_timer()
            return

        self._transition_fsm(
            STATE_READY,
            EVENT_COOLDOWN_ELAPSED,
            reason="ready_pending_cooldown_elapsed",
        )
        logger.info("READY_PENDING_COMPLETE -> READY")
        self._stop_ready_pending_cooldown_timer()

    def _start_ready_pending_cooldown_timer(self):
        self._stop_ready_pending_cooldown_timer()
        self._ready_pending_cooldown_timer.start(self._ready_pending_cooldown_ms)

        logger.info(
            "READY_PENDING_COOLDOWN_TIMER_STARTED cooldown_ms=%s",
            self._ready_pending_cooldown_ms,
        )

    def _stop_ready_pending_cooldown_timer(self):
        if self._ready_pending_cooldown_timer.isActive():
            self._ready_pending_cooldown_timer.stop()

    def _enter_blocked_state(self, reason: str, event: str = EVENT_CRITICAL_ERROR):
        self._stop_reconnect_timer()
        self._stop_ready_pending_cooldown_timer()

        if self.recovery_state != STATE_BLOCKED:
            self._transition_fsm(
                STATE_BLOCKED,
                event,
                reason=reason,
                allow_noop=True,
            )

        if self.risk_manager is not None:
            self.risk_manager.block_trading(reason)

    def _stop_reconnect_timer(self):
        if self._reconnect_timer.isActive():
            self._reconnect_timer.stop()

    def get_recovery_state(self) -> dict:
        return {
            "recovery_state": self.recovery_state,
            "reconnect_attempts": self._reconnect_attempts,
            "reconnect_max_attempts": self._reconnect_max_attempts,
            "account": self.account,
            "fsm": self.recovery_fsm.get_last_transition_snapshot(),
            "pending_intents": list(self._pending_intents.keys()),
        }

    def _transition_fsm(
        self,
        new_state: str,
        event: str,
        reason: str,
        allow_noop: bool = False,
    ):
        current_state = self.recovery_state

        if allow_noop and current_state == new_state:
            logger.info(
                "FSM_TRANSITION_NOOP state=%s event=%s reason=%s",
                current_state,
                event,
                reason,
            )
            return None

        try:
            return self.recovery_fsm.transition(
                new_state=new_state,
                event=event,
                reason=reason,
            )
        except ValueError:
            logger.exception(
                "FSM_TRANSITION_FAILED current_state=%s new_state=%s event=%s reason=%s",
                current_state,
                new_state,
                event,
                reason,
            )
            raise

    # ----------------------------------
    # Order
    # ----------------------------------

    def send_order(self, order, account_type="paper"):
        """
        정책:
        - READY: BUY/SELL 허용
        - EXIT_ONLY: SELL 허용 (기존 포지션 감소 방향만)
        - 그 외: 전면 차단
        """

        if not self.account:
            logger.error(
                "ORDER_SEND_FAILED account is not initialized order=%s",
                order,
            )
            return -1

        if self.recovery_state == STATE_BLOCKED:
            logger.error(
                "ORDER_BLOCKED_RECOVERY_STATE state=%s order=%s",
                self.recovery_state,
                order,
            )
            return -1

        if self.recovery_state == STATE_EXIT_ONLY:
            if not self._is_exit_only_order(order):
                logger.error(
                    "ORDER_BLOCKED_EXIT_ONLY state=%s order=%s",
                    self.recovery_state,
                    order,
                )
                return -1
        elif self.recovery_state != STATE_READY:
            logger.error(
                "ORDER_BLOCKED_RECOVERY_STATE state=%s order=%s",
                self.recovery_state,
                order,
            )
            return -1

        decision = self.order_guard.evaluate(account_type=account_type)

        if not decision.allowed:
            logger.warning(
                "ORDER_BLOCKED mode=%s account_type=%s reason=%s order=%s",
                decision.mode,
                decision.account_type,
                decision.reason,
                order,
            )
            return self.order_guard.build_block_response(
                decision=decision,
                order=order,
            )

        screen = "3000"

        side = str(getattr(order, "side", "BUY")).upper().strip()
        order_type = str(getattr(order, "order_type", "LIMIT")).upper().strip()
        intent_id = str(getattr(order, "intent_id", "") or "").strip()

        if side not in {"BUY", "SELL"}:
            logger.error(
                "ORDER_SEND_FAILED invalid side=%s order=%s",
                side,
                order,
            )
            return -1

        if not intent_id:
            logger.error("ORDER_SEND_FAILED missing intent_id order=%s", order)
            return -1

        n_order_type = 1 if side == "BUY" else 2

        if order_type == "MARKET":
            price = 0
            hoga_gb = "03"
        elif order_type == "LIMIT":
            try:
                price = int(getattr(order, "price", 0))
            except (TypeError, ValueError):
                logger.error(
                    "ORDER_SEND_FAILED invalid limit price order=%s",
                    order,
                )
                return -1

            if price <= 0:
                logger.error(
                    "ORDER_SEND_FAILED non_positive_limit_price=%s order=%s",
                    price,
                    order,
                )
                return -1

            hoga_gb = "00"
        else:
            logger.error(
                "ORDER_SEND_FAILED invalid order_type=%s order=%s",
                order_type,
                order,
            )
            return -1

        ret = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                "ORDER_REQ",
                screen,
                self.account,
                n_order_type,
                order.symbol,
                int(order.qty),
                price,
                hoga_gb,
                "",
            ],
        )

        logger.info(
            "SendOrder intent=%s symbol=%s side=%s qty=%s price=%s order_type=%s hoga=%s ret=%s account_type=%s recovery_state=%s",
            intent_id,
            order.symbol,
            side,
            order.qty,
            price,
            order_type,
            hoga_gb,
            ret,
            account_type,
            self.recovery_state,
        )

        if ret == 0:
            self._pending_intents[intent_id] = {
                "symbol": str(getattr(order, "symbol", "")).strip(),
                "side": side,
                "order": order,
            }

        return ret

    def _is_exit_only_order(self, order) -> bool:
        side = str(getattr(order, "side", "")).strip().upper()
        symbol = str(getattr(order, "symbol", "")).strip()

        if side != "SELL":
            return False

        qty_raw = getattr(order, "qty", None)
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            return False

        if qty <= 0:
            return False

        snapshot_fn = getattr(self.position_manager, "get_position_snapshot", None)
        if not callable(snapshot_fn):
            logger.error("EXIT_ONLY_POSITION_API_MISSING symbol=%s", symbol)
            return True

        try:
            snapshot = snapshot_fn(symbol)
        except Exception:
            logger.exception("EXIT_ONLY_POSITION_READ_FAILED symbol=%s", symbol)
            return True

        if not isinstance(snapshot, dict):
            logger.error("EXIT_ONLY_POSITION_UNKNOWN symbol=%s snapshot=%s", symbol, snapshot)
            return True

        try:
            current_qty = int(snapshot.get("qty", 0))
        except Exception:
            logger.error("EXIT_ONLY_POSITION_QTY_PARSE_FAILED symbol=%s snapshot=%s", symbol, snapshot)
            return True

        return 0 < qty <= current_qty

    # ----------------------------------
    # Account Positions TR
    # ----------------------------------

    def request_account_positions(self, account_no):
        """
        정책:
        - sync TR은 recovery validation 경로에서만 허용
        """
        if self.recovery_state != STATE_RECOVERING:
            raise RuntimeError(
                f"request_account_positions is only allowed during RECOVERING state, current={self.recovery_state}"
            )

        account_no = str(account_no).strip()
        if not account_no:
            raise ValueError("account_no is required")

        self._account_positions_rows = []
        self._account_positions_next = "0"

        self._request_account_positions_page(
            account_no=account_no,
            prev_next="0",
        )

        while self._account_positions_next == "2":
            self._request_account_positions_page(
                account_no=account_no,
                prev_next="2",
            )

        logger.info(
            "ACCOUNT_POSITIONS_FETCHED account=%s rows=%s",
            account_no,
            len(self._account_positions_rows),
        )

        return list(self._account_positions_rows)

    def _request_account_positions_page(self, account_no, prev_next="0"):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_no)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        rqname = self._account_positions_rqname
        trcode = "opw00018"
        screen_no = "9100"

        self._tr_error = None

        ret = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            rqname,
            trcode,
            int(prev_next),
            screen_no,
        )

        if ret != 0:
            raise RuntimeError(f"CommRqData(opw00018) failed ret={ret}")

        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

        if self._tr_error is not None:
            raise RuntimeError(self._tr_error)

    def _on_receive_tr_data(
        self,
        screen_no,
        rqname,
        trcode,
        record_name,
        prev_next,
        data_len,
        err_code,
        msg1,
        msg2,
    ):
        if rqname != self._account_positions_rqname:
            return

        try:
            self._account_positions_next = str(prev_next).strip()

            count = self.ocx.dynamicCall(
                "GetRepeatCnt(QString, QString)",
                trcode,
                rqname,
            )

            for i in range(int(count)):
                symbol = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    trcode,
                    rqname,
                    i,
                    "종목번호",
                ).strip()

                qty = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    trcode,
                    rqname,
                    i,
                    "보유수량",
                ).strip()

                avg_price = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    trcode,
                    rqname,
                    i,
                    "매입가",
                ).strip()

                self._account_positions_rows.append(
                    {
                        "symbol": symbol,
                        "qty": qty,
                        "avg_price": avg_price,
                    }
                )

            logger.info(
                "ACCOUNT_POSITIONS_TR_RECEIVED rows=%s prev_next=%s total=%s",
                int(count),
                self._account_positions_next,
                len(self._account_positions_rows),
            )

        except Exception as exc:
            self._tr_error = f"ACCOUNT_POSITIONS_TR_PARSE_FAILED: {exc}"
            logger.exception("ACCOUNT_POSITIONS_TR_PARSE_FAILED")
        finally:
            if self.tr_event_loop is not None:
                self.tr_event_loop.exit()
                self.tr_event_loop = None

    # ----------------------------------
    # Message Event
    # ----------------------------------

    def _on_receive_msg(self, screen, rqname, trcode, msg):
        logger.info("OnReceiveMsg %s", msg)

        if self._is_disconnect_message(msg):
            self._handle_disconnect("BROKER_MESSAGE_DISCONNECT")

    def _is_disconnect_message(self, msg) -> bool:
        text = str(msg or "").strip()

        if not text:
            return False

        disconnect_patterns = [
            "통신 연결이 끊",
            "연결이 끊",
            "접속이 종료",
            "서버와의 연결이 종료",
            "통신장애",
            "서버접속 실패",
            "통신 실패",
        ]

        return any(pattern in text for pattern in disconnect_patterns)

    # ----------------------------------
    # Real-time Event
    # ----------------------------------

    def _on_receive_real(self, code, real_type, real_data):
        logger.debug("REAL_EVENT code=%s type=%s", code, real_type)

        if not self.real_router:
            return

        self.real_router.on_receive_real_data(
            code,
            real_type,
            real_data,
            self,
        )

    # ----------------------------------
    # Chejan helpers
    # ----------------------------------

    def _normalize_chejan_side(self, side_raw: str) -> str:
        text = str(side_raw or "").strip().upper()

        if text in {"1", "+매수", "매수", "BUY"}:
            return "BUY"

        if text in {"2", "-매도", "매도", "SELL"}:
            return "SELL"

        return text

    def _parse_non_negative_int(self, raw_value, default=None):
        text = str(raw_value).strip() if raw_value is not None else ""
        if not text:
            return default

        try:
            value = int(text)
        except (TypeError, ValueError):
            return default

        if value < 0:
            return default

        return value

    def _is_ack_event(self, raw: dict) -> bool:
        """
        키움 chejan raw에서 '주문 접수/확인' 성격 이벤트인지 보수적으로 판별.

        원칙:
        - order_no가 있어야 함
        - order_status_raw가 있어야 함
        - fill_qty가 비어 있거나 0
        """
        if not isinstance(raw, dict):
            return False

        broker_order_id = str(raw.get("order_no", "")).strip()
        if not broker_order_id:
            return False

        order_status_raw = str(raw.get("order_status_raw", "")).strip()
        if not order_status_raw:
            return False

        fill_qty = self._parse_non_negative_int(raw.get("fill_qty_raw"), default=0)
        return fill_qty == 0

    def _route_fill_to_order_event_bridge(self, fill_event, raw: dict):
        if self.order_event_bridge is None:
            return

        broker_order_id = str(getattr(fill_event, "order_no", "")).strip()
        if not broker_order_id:
            return

        symbol = str(getattr(fill_event.key, "symbol", "")).strip()
        side = str(getattr(fill_event, "side", "")).strip().upper()
        filled_qty = self._parse_non_negative_int(
            getattr(fill_event, "fill_qty", None),
            default=None,
        )

        if filled_qty is None or filled_qty <= 0:
            return

        remaining_qty = self._parse_non_negative_int(
            raw.get("unfilled_qty_raw"),
            default=None,
        )

        payload = {
            "source": "kiwoom_chejan",
            "symbol": symbol,
            "side": side,
            "order_no": broker_order_id,
            "order_status_raw": raw.get("order_status_raw"),
            "orig_order_no": raw.get("orig_order_no"),
        }

        try:
            if remaining_qty is None:
                logger.debug(
                    "ORDER_FILL_BRIDGE_SKIPPED remaining_qty_unknown order_no=%s",
                    broker_order_id,
                )
                return

            if remaining_qty == 0:
                self.order_event_bridge.handle_full_fill(
                    broker_order_id=broker_order_id,
                    filled_qty=filled_qty,
                    intent_id=None,
                    reason="full_fill",
                    payload=payload,
                )
                return

            self.order_event_bridge.handle_partial_fill(
                broker_order_id=broker_order_id,
                filled_qty=filled_qty,
                remaining_qty=remaining_qty,
                intent_id=None,
                reason="partial_fill",
                payload=payload,
            )
        except Exception:
            logger.exception(
                "ORDER_FILL_BRIDGE_FAILED order_no=%s",
                broker_order_id,
            )

    # ----------------------------------
    # Chejan Event
    # ----------------------------------

    def _on_receive_chejan(self, gubun, item_cnt, fid_list):
        if gubun != "0":
            logger.debug(
                "CHEJAN_IGNORED gubun=%s item_cnt=%s fid_list=%s",
                gubun,
                item_cnt,
                fid_list,
            )
            return

        def fid_getter(fid: int):
            return self.ocx.dynamicCall("GetChejanData(int)", fid)

        raw = self.chejan_parser.parse(fid_getter)

        logger.debug("CHEJAN_RAW %s", raw)

        broker_order_id = str(raw.get("order_no", "")).strip()
        symbol = str(raw.get("symbol", "")).strip()
        side = self._normalize_chejan_side(raw.get("side_raw"))

        matched_intent_id = None
        if broker_order_id:
            matched_intent_id = self._bind_pending_intent_by_chejan(
                broker_order_id=broker_order_id,
                symbol=symbol,
                side=side,
            )

            if matched_intent_id:
                logger.debug(
                    "CHEJAN_BOUND_PENDING_INTENT intent=%s broker_id=%s symbol=%s",
                    matched_intent_id,
                    broker_order_id,
                    symbol,
                )

        # ----------------------------------
        # ACK / order accept path
        # ----------------------------------
        if self._is_ack_event(raw):
            logger.info(
                "CHEJAN_ACK_DETECTED broker_order_id=%s symbol=%s order_status_raw=%s",
                broker_order_id,
                symbol,
                raw.get("order_status_raw"),
            )

            try:
                if self.order_event_bridge is not None and broker_order_id:
                    self.order_event_bridge.handle_order_ack(
                        broker_order_id=broker_order_id,
                        intent_id=matched_intent_id,
                        reason="broker_ack",
                        payload={
                            "source": "kiwoom_chejan",
                            "symbol": symbol,
                            "side": side,
                            "order_status_raw": raw.get("order_status_raw"),
                            "order_qty_raw": raw.get("order_qty_raw"),
                            "unfilled_qty_raw": raw.get("unfilled_qty_raw"),
                            "order_price_raw": raw.get("order_price_raw"),
                            "orig_order_no": raw.get("orig_order_no"),
                        },
                    )
            except Exception:
                logger.exception(
                    "ORDER_ACK_BRIDGE_FAILED broker_order_id=%s symbol=%s",
                    broker_order_id,
                    symbol,
                )

        # ----------------------------------
        # Fill path
        # ----------------------------------
        fill_event = self.fill_normalizer.normalize_kiwoom_fill(raw)

        if not fill_event:
            return

        logger.info(
            "CHEJAN_FILL_NORMALIZED key=%s side=%s qty=%s price=%s order_no=%s exchange_time=%s ingest_time=%s",
            fill_event.key.to_serial(),
            fill_event.side,
            fill_event.fill_qty,
            fill_event.fill_price,
            fill_event.order_no,
            fill_event.exchange_time.isoformat(),
            fill_event.ingest_time.isoformat(),
        )

        self._route_fill_to_order_event_bridge(fill_event, raw)

        try:
            appended = self.fill_store.append(fill_event, raw_event=raw)
        except Exception:
            logger.exception(
                "FILL_LEDGER_APPEND_FAILED key=%s order_no=%s",
                fill_event.key.to_serial(),
                fill_event.order_no,
            )
            return

        if not appended:
            logger.warning(
                "DUPLICATE_FILL_IGNORED key=%s order_no=%s",
                fill_event.key.to_serial(),
                fill_event.order_no,
            )
            return

        try:
            apply_fill_result = self.position_manager.apply_fill(fill_event)
        except Exception:
            logger.exception(
                "POSITION_APPLY_FAILED key=%s order_no=%s",
                fill_event.key.to_serial(),
                fill_event.order_no,
            )
            return

        try:
            if self.risk_manager is not None:
                self.risk_manager.on_fill(
                    fill_event=fill_event,
                    apply_fill_result=apply_fill_result,
                )
        except Exception:
            logger.exception(
                "RISK_ON_FILL_FAILED key=%s order_no=%s",
                fill_event.key.to_serial(),
                fill_event.order_no,
            )
            return

        try:
            if self.execution_controller is not None:
                broker_order_id = str(fill_event.order_no).strip()
                symbol = str(fill_event.key.symbol).strip()

                if broker_order_id and matched_intent_id is None:
                    matched_intent_id = self._bind_pending_intent_by_chejan(
                        broker_order_id=broker_order_id,
                        symbol=symbol,
                        side=str(fill_event.side).strip().upper(),
                    )

                    if matched_intent_id:
                        logger.debug(
                            "CHEJAN_BOUND_PENDING_INTENT intent=%s broker_id=%s symbol=%s",
                            matched_intent_id,
                            broker_order_id,
                            symbol,
                        )

                if broker_order_id:
                    self.execution_controller.mark_order_closed_by_broker_order_id(
                        broker_order_id,
                        symbol,
                    )

        except Exception:
            logger.exception(
                "EXECUTION_CONTROLLER_CHEJAN_CLEANUP_FAILED order_no=%s",
                fill_event.order_no,
            )

        logger.debug(
            "POSITION_SNAPSHOT_AFTER_FILL %s",
            self.position_manager.snapshot(),
        )

    def _bind_pending_intent_by_chejan(self, broker_order_id: str, symbol: str, side: str):
        broker_order_id = str(broker_order_id).strip()
        symbol = str(symbol).strip()
        side = str(side).strip().upper()

        if not broker_order_id or not symbol or side not in {"BUY", "SELL"}:
            return None

        for intent_id, info in list(self._pending_intents.items()):
            pending_symbol = str(info.get("symbol", "")).strip()
            pending_side = str(info.get("side", "")).strip().upper()
            order = info.get("order")

            if pending_symbol != symbol:
                continue

            if pending_side != side:
                continue

            if self.execution_controller is not None:
                self.execution_controller.bind_broker_order_id(
                    intent_id,
                    broker_order_id,
                )

            if order is not None:
                try:
                    setattr(order, "broker_order_id", broker_order_id)
                except Exception:
                    logger.exception(
                        "PENDING_ORDER_BIND_FAILED intent=%s broker_id=%s",
                        intent_id,
                        broker_order_id,
                    )

            del self._pending_intents[intent_id]
            return intent_id

        logger.debug(
            "CHEJAN_PENDING_INTENT_NO_MATCH broker_id=%s symbol=%s side=%s pending_count=%s",
            broker_order_id,
            symbol,
            side,
            len(self._pending_intents),
        )
        return None

    # ----------------------------------
    # Error hooks
    # ----------------------------------

    def _on_fill_normalize_error(self, raw, exc):
        logger.error(
            "FILL_NORMALIZE_ERROR raw=%r error=%s",
            raw,
            exc,
            exc_info=True,
        )

    def _on_position_error(self, fill, exc):
        logger.error(
            "POSITION_ENGINE_ERROR fill=%s error=%s",
            fill,
            exc,
            exc_info=True,
        )