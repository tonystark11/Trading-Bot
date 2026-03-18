from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LOSS"}


class ValidationError(ValueError):
    pass


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s or not s.isalnum():
        raise ValidationError(f"Invalid symbol '{symbol}'. Must be alphanumeric, e.g. BTCUSDT.")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be BUY or SELL.")
    return s


def validate_order_type(order_type: str) -> str:
    ot = order_type.strip().upper()
    if ot not in VALID_ORDER_TYPES:
        raise ValidationError(f"Invalid order type '{order_type}'. Must be MARKET, LIMIT, or STOP_LOSS.")
    return ot


def validate_quantity(quantity) -> float:
    try:
        q = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if q <= 0:
        raise ValidationError(f"Quantity must be greater than 0.")
    return q


def validate_price(price, order_type: str):
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid price '{price}'.")
        if p <= 0:
            raise ValidationError("Price must be greater than 0.")
        return p
    return None


def validate_stop_price(stop_price, order_type: str):
    if order_type == "STOP_LOSS":
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP_LOSS orders.")
        try:
            sp = float(stop_price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid stop price '{stop_price}'.")
        if sp <= 0:
            raise ValidationError("Stop price must be greater than 0.")
        return sp
    return None
