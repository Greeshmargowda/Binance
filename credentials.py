"""
Order placement logic — sits between the CLI and the raw BinanceClient.

Responsibilities:
  - Build correct parameter dictionaries for each order type.
  - Format and print order summaries and responses.
  - Catch and re-raise errors with context.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import setup_logger

logger = setup_logger("orders")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(value: Any, decimals: int = 8) -> str:
    """Format a numeric value to `decimals` significant decimal places."""
    try:
        return f"{Decimal(str(value)):.{decimals}f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def _print_order_summary(params: Dict[str, Any]) -> None:
    """Pretty-print the order request parameters before submission."""
    print("\n" + "=" * 52)
    print("  ORDER REQUEST SUMMARY")
    print("=" * 52)
    for key, val in params.items():
        print(f"  {key:<18}: {val}")
    print("=" * 52)


def _print_order_response(resp: Dict[str, Any]) -> None:
    """Pretty-print the key fields from an order response."""
    print("\n" + "=" * 52)
    print("  ORDER RESPONSE")
    print("=" * 52)

    fields = [
        ("orderId",      resp.get("orderId",      "—")),
        ("symbol",       resp.get("symbol",       "—")),
        ("side",         resp.get("side",         "—")),
        ("type",         resp.get("type",         "—")),
        ("status",       resp.get("status",       "—")),
        ("origQty",      resp.get("origQty",      "—")),
        ("executedQty",  resp.get("executedQty",  "—")),
        ("avgPrice",     resp.get("avgPrice",     "—")),
        ("price",        resp.get("price",        "—")),
        ("stopPrice",    resp.get("stopPrice",    "—")),
        ("timeInForce",  resp.get("timeInForce",  "—")),
        ("updateTime",   resp.get("updateTime",   "—")),
    ]
    for label, value in fields:
        if value not in ("", "0", "0.00000000", None, "—") or label in ("orderId", "status"):
            print(f"  {label:<18}: {value}")

    print("=" * 52)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> Dict[str, Any]:
    """
    Place a MARKET order on Binance Futures Testnet.

    Args:
        client:   Authenticated BinanceClient instance.
        symbol:   Trading pair, e.g. "BTCUSDT".
        side:     "BUY" or "SELL".
        quantity: Order quantity (base asset).

    Returns:
        Raw order response dict from the API.
    """
    params: Dict[str, Any] = {
        "symbol":   symbol,
        "side":     side,
        "type":     "MARKET",
        "quantity": str(quantity),
    }

    logger.info("Placing MARKET order — %s %s qty=%s", side, symbol, quantity)
    _print_order_summary(params)

    try:
        resp = client.place_order(**params)
    except BinanceClientError as exc:
        logger.error("MARKET order failed — %s", exc)
        print(f"\n✗  Order FAILED: {exc}")
        raise

    logger.info(
        "MARKET order placed — orderId=%s status=%s executedQty=%s avgPrice=%s",
        resp.get("orderId"),
        resp.get("status"),
        resp.get("executedQty"),
        resp.get("avgPrice"),
    )
    _print_order_response(resp)
    print("\n✔  Order placed successfully!")
    return resp


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    Place a LIMIT order on Binance Futures Testnet.

    Args:
        client:        Authenticated BinanceClient instance.
        symbol:        Trading pair, e.g. "BTCUSDT".
        side:          "BUY" or "SELL".
        quantity:      Order quantity (base asset).
        price:         Limit price.
        time_in_force: "GTC" (default), "IOC", or "FOK".

    Returns:
        Raw order response dict from the API.
    """
    params: Dict[str, Any] = {
        "symbol":      symbol,
        "side":        side,
        "type":        "LIMIT",
        "quantity":    str(quantity),
        "price":       str(price),
        "timeInForce": time_in_force,
    }

    logger.info(
        "Placing LIMIT order — %s %s qty=%s price=%s tif=%s",
        side, symbol, quantity, price, time_in_force,
    )
    _print_order_summary(params)

    try:
        resp = client.place_order(**params)
    except BinanceClientError as exc:
        logger.error("LIMIT order failed — %s", exc)
        print(f"\n✗  Order FAILED: {exc}")
        raise

    logger.info(
        "LIMIT order placed — orderId=%s status=%s",
        resp.get("orderId"),
        resp.get("status"),
    )
    _print_order_response(resp)
    print("\n✔  Order placed successfully!")
    return resp


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> Dict[str, Any]:
    """
    Place a STOP_MARKET order (bonus order type) on Binance Futures Testnet.

    Args:
        client:     Authenticated BinanceClient instance.
        symbol:     Trading pair, e.g. "BTCUSDT".
        side:       "BUY" or "SELL".
        quantity:   Order quantity (base asset).
        stop_price: Trigger price for the stop.

    Returns:
        Raw order response dict from the API.
    """
    params: Dict[str, Any] = {
        "symbol":    symbol,
        "side":      side,
        "type":      "STOP_MARKET",
        "quantity":  str(quantity),
        "stopPrice": str(stop_price),
    }

    logger.info(
        "Placing STOP_MARKET order — %s %s qty=%s stopPrice=%s",
        side, symbol, quantity, stop_price,
    )
    _print_order_summary(params)

    try:
        resp = client.place_order(**params)
    except BinanceClientError as exc:
        logger.error("STOP_MARKET order failed — %s", exc)
        print(f"\n✗  Order FAILED: {exc}")
        raise

    logger.info(
        "STOP_MARKET order placed — orderId=%s status=%s",
        resp.get("orderId"),
        resp.get("status"),
    )
    _print_order_response(resp)
    print("\n✔  Order placed successfully!")
    return resp
