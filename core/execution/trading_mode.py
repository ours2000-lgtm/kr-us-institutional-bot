import os


class TradingMode:
    PAPER = "paper"
    LIVE = "live"


def get_trading_mode() -> str:
    """
    환경변수 기반 모드 결정
    기본값: paper (fail-safe)
    """
    mode = os.getenv("TRADING_MODE", TradingMode.PAPER)
    return str(mode).strip().lower()


def is_live_mode() -> bool:
    return get_trading_mode() == TradingMode.LIVE


def is_live_enabled() -> bool:
    """
    실전 주문 활성화 여부 (이중 안전장치)
    """
    return os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"


def validate_live_environment() -> bool:
    """
    추가 안전 체크
    production 환경에서만 live 허용
    """
    env = os.getenv("APP_ENV", "dev").lower()
    return env == "production"


def can_send_live_order(account_type: str):
    """
    실전 주문 가능 여부 판단

    반환:
        (허용 여부, 사유)
    """

    # Gate 1: mode
    if not is_live_mode():
        return False, "NOT_LIVE_MODE"

    # Gate 2: explicit enable
    if not is_live_enabled():
        return False, "LIVE_NOT_ENABLED"

    # Gate 3: account
    if str(account_type).lower() != "live":
        return False, "ACCOUNT_NOT_LIVE"

    # Gate 4: environment
    if not validate_live_environment():
        return False, "INVALID_ENVIRONMENT"

    return True, "OK"