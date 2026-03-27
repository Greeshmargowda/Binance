"""
Input validation for trading bot CLI arguments.
All validation raises ValueError with a human-readable message on failure.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP_LIMIT", "OCO", "TWAP", "GRID"}


def validate_symbol(symbol: str) -> str:
    """Return upper-cased symbol or raise ValueError."""
    symbol = symbol.strip().upper()
    if not symbol or not symbol.isalnum():
        raise ValueError(f"Invalid symbol '{symbol}'. Must be alphanumeric, e.g. BTCUSDT.")
    return symbol


def validate_side(side: str) -> str:
    """Return upper-cased side or raise ValueError."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}.")
    return side


def validate_order_type(order_type: str) -> str:
    """Return upper-cased order type or raise ValueError."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """Return positive Decimal quantity or raise ValueError."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be > 0, got {qty}.")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate price depending on order type.
    - LIMIT / STOP_MARKET: price is required and must be positive.
    - MARKET: price is ignored (returns None).
    """
    order_type = order_type.strip().upper()

    if order_type == "MARKET":
        return None  # price not applicable

    if price is None or str(price).strip() == "":
        raise ValueError(f"Price is required for {order_type} orders.")

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"Price must be > 0, got {p}.")
    return p


def validate_stop_price(stop_price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate stop price — only required for STOP_MARKET orders.
    """
    if order_type.upper() != "STOP_MARKET":
        return None

    if stop_price is None or str(stop_price).strip() == "":
        raise ValueError("Stop price is required for STOP_MARKET orders.")

    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be > 0, got {sp}.")
    return sp
