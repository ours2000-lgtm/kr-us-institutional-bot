# =====================================================================
# Executor Engine V10 — Smart Routing + Split Execution + Fail-Safe
# + Governance Hook (TraceBundle -> Evidence)
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable
import time

from pathlib import Path

from utils_v9 import safe_log
from price_optimizer_v10 import PriceOptimizerV10
from order_splitter_v10 import OrderSplitterV10
from execution_monitor_v10 import ExecutionMonitorV10


@dataclass
class ExecutionResult:
    success: bool
    filled_qty: float
    avg_price: float
    reason: str = ""


class ExecutorEngineV10:
    """
    기관급 Execution Engine V10

    기능 요약:
    - 최적 매수·매도 가격 산출 (microstructure 기반)
    - 주문 분할 (VWAP/TWAP 스타일)
    - 실시간 체결 모니터링 + Fail-safe
    - 슬리피지/가격 급등락 대응
    - 브로커 오류 자동 복구 + 재시도 로직

    Governance Hook:
    - execution intent / result를 TraceBundle로 기록하고,
      governance_validator + evidence_writer로 Evidence Artifact 생성.
    - GOV_EVIDENCE_MODE=HARD이면 evidence 실패 시 예외(FAIL-CLOSED).
      SOFT이면 로그만 남기고 계속 진행.
    """

    def __init__(self, broker, config: Dict[str, Any], price_feed_fn: Callable):
        self.broker = broker
        self.config = config
        self.price_feed_fn = price_feed_fn

        # 내부 엔진 구성
        self.optimizer = PriceOptimizerV10(config)
        self.splitter = OrderSplitterV10(config)
        self.monitor = ExecutionMonitorV10(config)

        self.max_retries = int(config.get("EXECUTOR", {}).get("max_retries", 3))

        # Governance config
        gov = config.get("GOVERNANCE", {}) if isinstance(config, dict) else {}
        self.gov_enabled = bool(gov.get("enabled", True))
        self.gov_actor_id = str(gov.get("actor_id", "EXECUTOR_V10"))
        self.gov_node_id = str(gov.get("node_id", "UNKNOWN_NODE"))
        self.gov_git_commit = str(gov.get("git_commit", "UNKNOWN_COMMIT"))
        self.gov_schema_set_ref = str(gov.get("schema_set_ref", "docs/schemas/v1"))

        # Runtime dirs (repo-relative)
        self.gov_traces_dir = Path(gov.get("traces_dir", "runtime/governance/traces"))
        self.gov_evidence_dir = Path(gov.get("evidence_dir", "runtime/evidence"))

    # -----------------------------------------------------------------
    # 내부 로그 함수
    # -----------------------------------------------------------------
    def _log(self, msg: str):
        safe_log(f"[EXECUTOR] {msg}")

    # -----------------------------------------------------------------
    # Governance emit + bridge (best-effort import)
    # -----------------------------------------------------------------
    def _governance_emit(self, *, event: str, decision: str, fail_closed: bool, reason_code: str, context: Dict[str, Any]) -> None:
        if not self.gov_enabled:
            return

        try:
            from runtime.governance.trace_emitter import emit_trace_bundle, write_trace_bundle
            from runtime.governance.governance_bridge import process_governance_evidence
        except Exception:
            # Fallback (if runtime/ is not a package in current exec mode)
            from runtime.governance.trace_emitter import emit_trace_bundle, write_trace_bundle  # type: ignore
            from runtime.governance.governance_bridge import process_governance_evidence  # type: ignore

        trace_bundle = emit_trace_bundle(
            decision=decision,
            fail_closed=fail_closed,
            reason_code=reason_code,
            actor_id=self.gov_actor_id,
            context={"event": event, **(context or {})},
            engine_version="executor_engine_v10",
            raw_reason=context.get("raw_reason") if isinstance(context, dict) else None,
            outcome=context.get("outcome") if isinstance(context, dict) else None,
        )

        trace_path = write_trace_bundle(trace_bundle, self.gov_traces_dir)

        # Evidence (HARD/SOFT is controlled by env GOV_EVIDENCE_MODE)
        res = process_governance_evidence(
            trace_bundle=trace_bundle,
            trace_path=trace_path,
            evidence_dir=self.gov_evidence_dir,
            schema_set_ref=self.gov_schema_set_ref,
            node_id=self.gov_node_id,
            git_commit=self.gov_git_commit,
        )

        if not res.success:
            # HARD면 여기서 RuntimeError가 raise됨. SOFT면 여기로 내려옴.
            self._log(f"[GOV][SOFT] evidence failed: {res.error}")
        else:
            # Optional: keep it quiet or log one line.
            self._log(f"[GOV] evidence ok: {res.evidence_path}")

    # =================================================================
    # 매수 엔진
    # =================================================================
    def buy(self, symbol: str, total_qty: float) -> ExecutionResult:

        self._log(f"매수 시작 → {symbol}, qty={total_qty:.2f}")

        if total_qty <= 0:
            return ExecutionResult(False, 0, 0, "qty<=0")

        # (1) 최적 매수가 계산
        last_price = self.price_feed_fn()
        opt_price = self.optimizer.best_buy_price(last_price)

        # Governance: intent (order attempt)
        self._governance_emit(
            event="EXECUTION_BUY_INTENT",
            decision="ALLOW",
            fail_closed=False,
            reason_code="EXECUTED_OK",
            context={
                "symbol": symbol,
                "total_qty": float(total_qty),
                "opt_price": float(opt_price),
            },
        )

        # (2) 분할 수량 계산
        split_orders = self.splitter.split_orders(total_qty)

        filled_total = 0.0
        weighted_price_sum = 0.0

        # (3) 분할 주문 실행 루프
        for i, part_qty in enumerate(split_orders):

            retries = 0
            last_filled = 0.0
            avg_fill_price = opt_price

            self._log(f"[BUY] Part {i+1}/{len(split_orders)} qty={part_qty:.2f}")

            while retries < self.max_retries:
                try:
                    order_id = self.broker.buy(symbol, part_qty, opt_price)
                    self._log(f"BUY submitted → id={order_id}")

                    fill = self.monitor.monitor_order(
                        order_id=order_id,
                        symbol=symbol,
                        ref_price=opt_price,
                        broker=self.broker,
                        price_feed_fn=self.price_feed_fn,
                        logger=self._log
                    )

                    if fill.filled_qty > 0:
                        last_filled = fill.filled_qty
                        avg_fill_price = fill.avg_fill_price
                        break

                    retries += 1
                    self._log(f"[RETRY BUY] attempt={retries}")
                    time.sleep(0.25)

                except Exception as e:
                    self._log(f"[BUY ERROR] {e}")
                    retries += 1
                    time.sleep(0.25)

            filled_total += last_filled
            weighted_price_sum += last_filled * avg_fill_price

        if filled_total > 0:
            final_price = weighted_price_sum / filled_total

            # Governance: result (executed)
            self._governance_emit(
                event="EXECUTION_BUY_RESULT",
                decision="ALLOW",
                fail_closed=False,
                reason_code="EXECUTED_OK",
                context={
                    "symbol": symbol,
                    "filled_qty": float(filled_total),
                    "avg_price": float(final_price),
                },
            )

            return ExecutionResult(True, filled_total, final_price)

        # Governance: result (failed)
        self._governance_emit(
            event="EXECUTION_BUY_RESULT",
            decision="DENY",
            fail_closed=True,
            reason_code="FAILED_INFRA_ERROR",
            context={
                "symbol": symbol,
                "filled_qty": 0.0,
                "avg_price": 0.0,
                "raw_reason": "no_fills",
            },
        )

        return ExecutionResult(False, 0, 0, "no fills")

    # =================================================================
    # 매도 엔진
    # =================================================================
    def sell(self, symbol: str, total_qty: float, ref_price: Optional[float] = None) -> ExecutionResult:

        self._log(f"매도 시작 → {symbol}, qty={total_qty:.2f}")

        if total_qty <= 0:
            return ExecutionResult(False, 0, 0, "qty<=0")

        last_price = ref_price if ref_price else self.price_feed_fn()
        opt_price = self.optimizer.best_sell_price(last_price)

        # Governance: intent
        self._governance_emit(
            event="EXECUTION_SELL_INTENT",
            decision="ALLOW",
            fail_closed=False,
            reason_code="EXECUTED_OK",
            context={
                "symbol": symbol,
                "total_qty": float(total_qty),
                "opt_price": float(opt_price),
            },
        )

        split_orders = self.splitter.split_orders(total_qty)

        filled_total = 0.0
        weighted_price_sum = 0.0

        for i, part_qty in enumerate(split_orders):

            retries = 0
            last_filled = 0.0
            avg_fill_price = opt_price

            self._log(f"[SELL] Part {i+1}/{len(split_orders)} qty={part_qty:.2f}")

            while retries < self.max_retries:
                try:
                    order_id = self.broker.sell(symbol, part_qty, opt_price)
                    self._log(f"SELL submitted → id={order_id}")

                    fill = self.monitor.monitor_order(
                        order_id=order_id,
                        symbol=symbol,
                        ref_price=opt_price,
                        broker=self.broker,
                        price_feed_fn=self.price_feed_fn,
                        logger=self._log
                    )

                    if fill.filled_qty > 0:
                        last_filled = fill.filled_qty
                        avg_fill_price = fill.avg_fill_price
                        break

                    retries += 1
                    self._log(f"[RETRY SELL] attempt={retries}")
                    time.sleep(0.25)

                except Exception as e:
                    self._log(f"[SELL ERROR] {e}")
                    retries += 1
                    time.sleep(0.25)

            filled_total += last_filled
            weighted_price_sum += last_filled * avg_fill_price

        if filled_total > 0:
            final_price = weighted_price_sum / filled_total

            # Governance: result (executed)
            self._governance_emit(
                event="EXECUTION_SELL_RESULT",
                decision="ALLOW",
                fail_closed=False,
                reason_code="EXECUTED_OK",
                context={
                    "symbol": symbol,
                    "filled_qty": float(filled_total),
                    "avg_price": float(final_price),
                },
            )

            return ExecutionResult(True, filled_total, final_price)

        # Governance: result (failed)
        self._governance_emit(
            event="EXECUTION_SELL_RESULT",
            decision="DENY",
            fail_closed=True,
            reason_code="FAILED_INFRA_ERROR",
            context={
                "symbol": symbol,
                "filled_qty": 0.0,
                "avg_price": 0.0,
                "raw_reason": "no_fills",
            },
        )

        return ExecutionResult(False, 0, 0, "no fills")
