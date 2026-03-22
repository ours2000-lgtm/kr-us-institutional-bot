# path: engine/manual_recovery_controller.py

from __future__ import annotations

from logging import getLogger


logger = getLogger(__name__)


class ManualRecoveryController:
    """
    BLOCKED 상태 수동 해제

    정책:
    - operator가 명시적으로 호출
    - risk block 해제
    - FSM reset
    """

    def __init__(self, adapter, risk_manager=None):
        self.adapter = adapter
        self.risk_manager = risk_manager

    # =====================================================
    # PUBLIC
    # =====================================================

    def manual_unblock(self, reason: str = "manual_unblock"):
        logger.warning("MANUAL_UNBLOCK_REQUEST reason=%s", reason)

        # 1) FSM reset
        try:
            if hasattr(self.adapter, "manual_unblock"):
                self.adapter.manual_unblock()
            else:
                logger.error("ADAPTER_MANUAL_UNBLOCK_NOT_SUPPORTED")
                return False
        except Exception:
            logger.exception("MANUAL_UNBLOCK_FSM_FAILED")
            return False

        # 2) risk 해제
        if self.risk_manager is not None:
            try:
                self.risk_manager.clear_block(reason)
            except Exception:
                logger.exception("MANUAL_UNBLOCK_RISK_FAILED")
                return False

        logger.warning("SYSTEM_UNBLOCKED_SUCCESSFULLY")

        return True