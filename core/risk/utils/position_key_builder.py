from typing import Any

from engine.position_key import PositionKey


class PositionKeyBuildError(Exception):
    pass


def _normalize_text(value: Any, field_name: str) -> str:
    if value is None:
        raise PositionKeyBuildError(f"{field_name} is required")

    text = str(value).strip()
    if not text:
        raise PositionKeyBuildError(f"{field_name} is empty")

    return text


def build_position_key(order) -> PositionKey:
    """
    RiskManager v2 PositionKey 생성 규약 (SSOT)

    입력:
        order 객체에서 아래 필드를 읽는다:
        - account_no
        - symbol
        - exchange
        - instrument_type

    정규화 정책:
        - 모든 텍스트 필드 strip()
        - symbol / exchange / instrument_type → upper()
        - 빈 문자열 / None → 예외

    호출 시점:
        - 반드시 order validation 통과 이후 호출
        - invalid input 상태에서 호출 금지

    예외 정책:
        - 필드 누락 / 빈 값 → PositionKeyBuildError 발생
    """

    try:
        account_no = _normalize_text(
            getattr(order, "account_no", None),
            "account_no",
        )

        symbol = _normalize_text(
            getattr(order, "symbol", None),
            "symbol",
        ).upper()

        exchange = _normalize_text(
            getattr(order, "exchange", None),
            "exchange",
        ).upper()

        instrument_type = _normalize_text(
            getattr(order, "instrument_type", None),
            "instrument_type",
        ).upper()

    except Exception as exc:
        raise PositionKeyBuildError(str(exc)) from exc

    return PositionKey(
        account_no=account_no,
        symbol=symbol,
        exchange=exchange,
        instrument_type=instrument_type,
    )