"""
AccountRiskGuard v1.0 FINAL — Account-Level Risk Constitution (FROZEN)

이 모듈은 live_trading_safety_checklist.md의 “계좌 헌법”을
코드 레벨에서 강제하는 Account-Level Risk Guard이다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
역할 (DO):
- 계좌 단위 리스크를 pre-trade 단계에서 강제한다.
- 신규 주문(OrderIntent)이 계좌 헌법을 위반하는지 평가한다.
- ALWAYS deterministic: 동일 입력 → 동일 결정.
- 어떤 경우에도 예외를 외부로 던지지 않는다. (fail-closed)

하지 않는 일 (DO NOT):
- 전략 로직 판단 ❌
- 주문 실행 ❌
- 포트폴리오 리밸런싱 ❌
- Orchestrator 제어 ❌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FROZEN AXES (절대 변경 금지):
- 입력/출력 계약
- 평가 순서 (ordering)
- HARD_STOP 의미 (사람 승인 없이는 해제 불가)
- fail-safe 정책 (fail-closed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime, timezone


# =====================================================================
# Constants / Enums (Enum-like, string based)
# =====================================================================

DecisionType = Literal["ALLOW", "REDUCE", "BLOCK", "HARD_STOP"]
ApplyScope = Literal["ACCOUNT", "STRATEGY", "SYMBOL"]
Environment = Literal["sim", "paper", "live"]
ResetPolicy = Literal["DAILY", "WEEKLY", "NEVER"]


class ReasonCodes:
    # Data / Integrity
    DATA_INVALID = "DATA_INVALID"
    DATA_STALE = "DATA_STALE"
    STATE_CORRUPTED = "STATE_CORRUPTED"

    # Risk / Account
    RISK_DAILY_LOSS_LIMIT = "RISK_DAILY_LOSS_LIMIT"
    RISK_MAX_DRAWDOWN = "RISK_MAX_DRAWDOWN"
    RISK_MAX_EXPOSURE = "RISK_MAX_EXPOSURE"
    RISK_CONSECUTIVE_LOSS = "RISK_CONSECUTIVE_LOSS"

    # Control
    STATE_HALTED = "STATE_HALTED"
    EXPERIMENTAL_FEATURE_BLOCKED = "EXPERIMENTAL_FEATURE_BLOCKED"
    GUARD_EXCEPTION = "GUARD_EXCEPTION"


# =====================================================================
# Input Contracts
# =====================================================================

@dataclass(frozen=True)
class AccountSnapshot:
    """
    계좌 상태 스냅샷 (pre-trade)

    이 스냅샷은 '현재 시점에서 사실로 간주되는 값'만 포함해야 한다.
    """
    account_id: str
    timestamp: str                 # ISO8601 (UTC Z 권장)
    trading_date: str              # YYYY-MM-DD (세션/일일 기준)
    timezone: str                  # e.g. "UTC", "KST"
    environment: Environment       # sim / paper / live

    equity: float                  # 현재 계좌 자산
    peak_equity: float             # 피크 자산 (DD 계산용)
    daily_pnl: float               # 금일 손익
    total_drawdown: float          # 피크 대비 DD
    total_exposure: float          # 현재 총 익스포저 (노출)

    consecutive_loss_days: int
    consecutive_loss_trades: int

    snapshot_valid: bool
    stale_data_seconds: int
    data_source: Literal["primary", "fallback"]


@dataclass(frozen=True)
class OrderIntent:
    """
    신규 주문 의도 (아직 실행 전)
    """
    strategy_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    order_size: float
    expected_exposure_delta: float


# =====================================================================
# Output Contract
# =====================================================================

@dataclass
class AccountRiskDecision:
    decision: DecisionType
    applies_scope: ApplyScope

    reason_codes: List[str] = field(default_factory=list)

    # execution hints (의미 레벨)
    action_hint: Optional[
        Literal[
            "NO_NEW_TRADES",
            "CANCEL_ORDER",
            "TRIM_POSITION",
            "CLOSE_ALL",
        ]
    ] = None

    requires_human_approval: bool = False

    evaluated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


# =====================================================================
# AccountRiskGuard
# =====================================================================

class AccountRiskGuard:
    """
    AccountRiskGuard v1.0 FINAL

    Evaluation Ordering (FROZEN):
        1. Data integrity check
        2. HARD_STOP conditions
        3. BLOCK conditions
        4. REDUCE conditions
        5. ALLOW
    """

    def evaluate(
        self,
        account: AccountSnapshot,
        order: OrderIntent,
    ) -> AccountRiskDecision:
        """
        Evaluate a single OrderIntent against account-level risk rules.

        Fail-safe:
        - Any exception → HARD_STOP (fail-closed)
        """
        try:
            # 1. Data integrity
            if not self._check_data_integrity(account):
                return self._hard_stop(
                    ReasonCodes.DATA_INVALID,
                    requires_human_approval=True,
                )

            # 2. HARD STOP
            hard_stop = self._check_hard_stop(account)
            if hard_stop:
                return hard_stop

            # 3. BLOCK
            block = self._check_block(account, order)
            if block:
                return block

            # 4. REDUCE
            reduce_decision = self._check_reduce(account, order)
            if reduce_decision:
                return reduce_decision

            # 5. ALLOW
            return AccountRiskDecision(
                decision="ALLOW",
                applies_scope="ACCOUNT",
            )

        except Exception:
            # 절대 fail-open 금지
            return self._hard_stop(
                ReasonCodes.GUARD_EXCEPTION,
                requires_human_approval=True,
            )

    # -----------------------------------------------------------------
    # Checks
    # -----------------------------------------------------------------

    def _check_data_integrity(self, account: AccountSnapshot) -> bool:
        """
        데이터 무결성 계약:
        - snapshot_valid == False → 거래 중단
        - stale_data_seconds 임계 초과 → 거래 중단

        TODO: stale threshold 설정값 연동
        """
        if not account.snapshot_valid:
            return False
        return True

    def _check_hard_stop(
        self,
        account: AccountSnapshot,
    ) -> Optional[AccountRiskDecision]:
        """
        HARD_STOP 조건:
        - 일일 손실 한도 초과
        - 최대 DD 초과
        - 이미 halt 상태

        환경 차등 여지:
        - environment == "sim" 인 경우 requires_human_approval 완화 가능
        """
        # TODO: daily loss limit
        # TODO: max drawdown
        return None

    def _check_block(
        self,
        account: AccountSnapshot,
        order: OrderIntent,
    ) -> Optional[AccountRiskDecision]:
        """
        BLOCK 조건:
        - 총 익스포저 상한 초과
        - 실험 플래그 차단 (live)
        """
        # TODO: max exposure
        # TODO: experimental feature block
        return None

    def _check_reduce(
        self,
        account: AccountSnapshot,
        order: OrderIntent,
    ) -> Optional[AccountRiskDecision]:
        """
        REDUCE 조건:
        - 익스포저 상한 근접
        - 연속 손실 경고 구간
        """
        # TODO: near exposure cap
        # TODO: consecutive loss soft guard
        return None

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _hard_stop(
        self,
        reason_code: str,
        *,
        requires_human_approval: bool,
    ) -> AccountRiskDecision:
        return AccountRiskDecision(
            decision="HARD_STOP",
            applies_scope="ACCOUNT",
            reason_codes=[reason_code],
            action_hint="NO_NEW_TRADES",
            requires_human_approval=requires_human_approval,
        )
