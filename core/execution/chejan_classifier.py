from typing import Optional, Tuple, Literal, Dict, Any

ChejanState = Literal["PENDING", "CONFIRMED", "IGNORED"]


def classify_chejan(data: Dict[str, Any]) -> Tuple[ChejanState, str]:

    # ---------------------------
    # normalize
    # ---------------------------
    raw_side = data.get("side")
    side = str(raw_side).strip().upper() if raw_side is not None else None

    raw_qty = data.get("fill_qty")
    raw_price = data.get("fill_price")

    order_no = data.get("order_no")
    symbol = data.get("symbol")

    # ---------------------------
    # 1. 필수 식별자
    # ---------------------------
    if not order_no or not symbol:
        return "IGNORED", "missing_identity"

    # ---------------------------
    # 2. side 검증
    # ---------------------------
    if side not in ("BUY", "SELL"):
        return "IGNORED", "invalid_side"

    # ---------------------------
    # 3. PENDING (미도착)
    # ---------------------------
    if raw_qty in (None, "", " ") or raw_price in (None, "", " "):
        return "PENDING", "missing_fill_fields"

    # ---------------------------
    # 4. 숫자 변환
    # ---------------------------
    try:
        qty = int(str(raw_qty).replace(",", "").strip())
        price = float(str(raw_price).replace(",", "").strip())
    except (TypeError, ValueError):
        return "IGNORED", "invalid_numeric_format"

    # ---------------------------
    # 5. 값 검증
    # ---------------------------
    if qty <= 0:
        return "IGNORED", "non_positive_qty"

    if price <= 0:
        return "IGNORED", "non_positive_price"

    return "CONFIRMED", "ok"