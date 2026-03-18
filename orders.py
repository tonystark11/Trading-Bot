from __future__ import annotations
from dataclasses import dataclass
from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.validators import (
    ValidationError, validate_order_type, validate_price,
    validate_quantity, validate_side, validate_stop_price, validate_symbol,
)

logger = setup_logging()


@dataclass
class OrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None = None
    stop_price: float | None = None


@dataclass
class OrderResult:
    success: bool
    order_id: int | None = None
    status: str | None = None
    executed_qty: str | None = None
    avg_price: str | None = None
    raw: dict | None = None
    error: str | None = None


def build_order_request(symbol, side, order_type, quantity, price=None, stop_price=None) -> OrderRequest:
    sym = validate_symbol(symbol)
    sid = validate_side(side)
    ot = validate_order_type(order_type)
    qty = validate_quantity(quantity)
    prc = validate_price(price, ot)
    stp = validate_stop_price(stop_price, ot)
    return OrderRequest(symbol=sym, side=sid, order_type=ot, quantity=qty, price=prc, stop_price=stp)


def place_order(client: BinanceClient, req: OrderRequest) -> OrderResult:
    try:
        raw = client.place_order(
            symbol=req.symbol,
            side=req.side,
            order_type=req.order_type,
            quantity=req.quantity,
            price=req.price,
            stop_price=req.stop_price,
        )
        return OrderResult(
            success=True,
            order_id=raw.get("orderId"),
            status=raw.get("status"),
            executed_qty=raw.get("executedQty"),
            avg_price=raw.get("avgPrice"),
            raw=raw,
        )
    except (BinanceClientError, ValidationError) as exc:
        logger.error(f"Order placement failed: {exc}")
        return OrderResult(success=False, error=str(exc))
