"""
Advanced order types: Stop-Limit, OCO, TWAP, Grid.

Each function follows the same contract as the base orders:
  - accepts a BinanceClient + validated params
  - logs at INFO / DEBUG
  - prints a formatted summary + response
  - raises BinanceClientError on API failure
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import setup_logger

logger = setup_logger("advanced_orders")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _print_block(title: str, rows: List[tuple]) -> None:
    width = 52
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)
    for label, value in rows:
        if value not in (None, "", "—"):
            print(f"  {label:<22}: {value}")
    print("=" * width)


def _response_rows(resp: Dict[str, Any]) -> List[tuple]:
    return [
        ("orderId",    resp.get("orderId",    "—")),
        ("symbol",     resp.get("symbol",     "—")),
        ("side",       resp.get("side",       "—")),
        ("type",       resp.get("type",       "—")),
        ("status",     resp.get("status",     "—")),
        ("origQty",    resp.get("origQty",    "—")),
        ("executedQty",resp.get("executedQty","—")),
        ("avgPrice",   resp.get("avgPrice",   "—")),
        ("price",      resp.get("price",      "—")),
        ("stopPrice",  resp.get("stopPrice",  "—")),
        ("timeInForce",resp.get("timeInForce","—")),
    ]


# ---------------------------------------------------------------------------
# 1. STOP-LIMIT
# ---------------------------------------------------------------------------


def place_stop_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    stop_price: Decimal,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    STOP order with a LIMIT fill price.

    The order is triggered when the market reaches `stop_price`,
    then placed as a LIMIT order at `price`.
    """
    params: Dict[str, Any] = {
        "symbol":      symbol,
        "side":        side,
        "type":        "STOP",
        "quantity":    str(quantity),
        "price":       str(price),
        "stopPrice":   str(stop_price),
        "timeInForce": time_in_force,
    }

    logger.info(
        "Placing STOP_LIMIT order — %s %s qty=%s price=%s stopPrice=%s",
        side, symbol, quantity, price, stop_price,
    )
    _print_block("STOP-LIMIT ORDER REQUEST", [
        ("symbol",       symbol),
        ("side",         side),
        ("quantity",     quantity),
        ("limit price",  price),
        ("stop trigger", stop_price),
        ("timeInForce",  time_in_force),
    ])

    try:
        resp = client.place_order(**params)
    except BinanceClientError as exc:
        logger.error("STOP_LIMIT order failed — %s", exc)
        print(f"\n✗  Order FAILED: {exc}")
        raise

    logger.info("STOP_LIMIT order placed — orderId=%s status=%s", resp.get("orderId"), resp.get("status"))
    _print_block("STOP-LIMIT ORDER RESPONSE", _response_rows(resp))
    print("\n✔  Stop-Limit order placed successfully!")
    return resp


# ---------------------------------------------------------------------------
# 2. OCO  (One-Cancels-the-Other)
# ---------------------------------------------------------------------------


def place_oco_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    stop_price: Decimal,
    stop_limit_price: Decimal,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    OCO order: a LIMIT order + a STOP-LIMIT order. Cancelling one cancels
    the other. Uses the Binance /fapi/v1/order/oco endpoint.

    Args:
        price:            Take-profit limit price.
        stop_price:       Stop trigger price.
        stop_limit_price: Limit price after stop is triggered.
    """
    params: Dict[str, Any] = {
        "symbol":           symbol,
        "side":             side,
        "quantity":         str(quantity),
        "price":            str(price),
        "stopPrice":        str(stop_price),
        "stopLimitPrice":   str(stop_limit_price),
        "stopLimitTimeInForce": time_in_force,
    }

    logger.info(
        "Placing OCO order — %s %s qty=%s price=%s stopPrice=%s stopLimitPrice=%s",
        side, symbol, quantity, price, stop_price, stop_limit_price,
    )
    _print_block("OCO ORDER REQUEST", [
        ("symbol",           symbol),
        ("side",             side),
        ("quantity",         quantity),
        ("take-profit price",price),
        ("stop trigger",     stop_price),
        ("stop limit price", stop_limit_price),
        ("timeInForce",      time_in_force),
    ])

    try:
        resp = client.place_order_raw("POST", "/fapi/v1/order/oco", params)
    except BinanceClientError as exc:
        logger.error("OCO order failed — %s", exc)
        print(f"\n✗  Order FAILED: {exc}")
        raise

    # OCO response has an 'orderReports' list
    order_list_id = resp.get("orderListId", "—")
    reports = resp.get("orderReports", [])
    logger.info("OCO order placed — orderListId=%s orders=%d", order_list_id, len(reports))

    _print_block("OCO ORDER RESPONSE", [
        ("orderListId",  order_list_id),
        ("contingencyType", resp.get("contingencyType", "—")),
        ("listStatusType",  resp.get("listStatusType",  "—")),
        ("listOrderStatus", resp.get("listOrderStatus", "—")),
    ])
    for i, r in enumerate(reports, 1):
        print(f"\n  — Leg {i}: orderId={r.get('orderId')}  type={r.get('type')}  status={r.get('status')}")

    print("\n✔  OCO order placed successfully!")
    return resp


# ---------------------------------------------------------------------------
# 3. TWAP  (Time-Weighted Average Price)
# ---------------------------------------------------------------------------


def place_twap_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    total_quantity: Decimal,
    slices: int,
    interval_seconds: int,
    order_type: str = "MARKET",
    price: Optional[Decimal] = None,
) -> List[Dict[str, Any]]:
    """
    Naive TWAP: splits `total_quantity` into `slices` equal child orders
    placed `interval_seconds` apart.

    Args:
        slices:           Number of child orders.
        interval_seconds: Delay between child orders (seconds).
        order_type:       "MARKET" (default) or "LIMIT" per slice.
        price:            Required when order_type="LIMIT".

    Returns:
        List of raw order response dicts, one per slice.
    """
    if slices < 2:
        raise ValueError("TWAP requires at least 2 slices.")
    if interval_seconds < 1:
        raise ValueError("Interval must be at least 1 second.")

    slice_qty = (total_quantity / Decimal(slices)).quantize(Decimal("0.00001"))

    logger.info(
        "Starting TWAP — %s %s totalQty=%s slices=%d interval=%ds",
        side, symbol, total_quantity, slices, interval_seconds,
    )
    _print_block("TWAP ORDER PLAN", [
        ("symbol",        symbol),
        ("side",          side),
        ("total quantity",total_quantity),
        ("slices",        slices),
        ("qty per slice", slice_qty),
        ("interval",      f"{interval_seconds}s"),
        ("child type",    order_type),
        ("limit price",   price if price else "—"),
        ("est. duration", f"{(slices - 1) * interval_seconds}s"),
    ])

    responses: List[Dict[str, Any]] = []

    for i in range(1, slices + 1):
        print(f"\n  ▶  Slice {i}/{slices}  qty={slice_qty} …", end=" ", flush=True)
        logger.info("TWAP slice %d/%d — qty=%s", i, slices, slice_qty)

        params: Dict[str, Any] = {
            "symbol":   symbol,
            "side":     side,
            "type":     order_type,
            "quantity": str(slice_qty),
        }
        if order_type == "LIMIT" and price:
            params["price"] = str(price)
            params["timeInForce"] = "GTC"

        try:
            resp = client.place_order(**params)
            responses.append(resp)
            status = resp.get("status", "?")
            print(f"orderId={resp.get('orderId')}  status={status}")
            logger.info("TWAP slice %d placed — orderId=%s status=%s", i, resp.get("orderId"), status)
        except BinanceClientError as exc:
            logger.error("TWAP slice %d failed — %s", i, exc)
            print(f"FAILED ({exc})")
            # Continue remaining slices rather than aborting the whole TWAP
            responses.append({"error": str(exc), "slice": i})

        if i < slices:
            time.sleep(interval_seconds)

    placed = sum(1 for r in responses if "orderId" in r)
    print(f"\n✔  TWAP complete — {placed}/{slices} slices placed successfully.")
    logger.info("TWAP finished — %d/%d slices succeeded", placed, slices)
    return responses


# ---------------------------------------------------------------------------
# 4. Grid
# ---------------------------------------------------------------------------


def place_grid_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity_per_level: Decimal,
    levels: int,
    start_price: Decimal,
    step: Decimal,
    time_in_force: str = "GTC",
) -> List[Dict[str, Any]]:
    """
    Grid strategy: place `levels` LIMIT orders evenly spaced by `step`.

    BUY grid  — prices step DOWN from start_price (accumulate on dips).
    SELL grid — prices step UP   from start_price (distribute on rallies).

    Args:
        levels:            Number of grid levels.
        start_price:       First grid price.
        step:              Price increment between levels (always positive).
        quantity_per_level:Quantity for each grid order.
    """
    if levels < 2:
        raise ValueError("Grid requires at least 2 levels.")
    if step <= 0:
        raise ValueError("Grid step must be positive.")

    direction = -1 if side.upper() == "BUY" else 1
    prices = [start_price + direction * step * i for i in range(levels)]

    logger.info(
        "Starting GRID — %s %s levels=%d start=%s step=%s",
        side, symbol, levels, start_price, step,
    )
    _print_block("GRID ORDER PLAN", [
        ("symbol",         symbol),
        ("side",           side),
        ("levels",         levels),
        ("qty/level",      quantity_per_level),
        ("start price",    start_price),
        ("step",           step),
        ("price range",    f"{min(prices)} → {max(prices)}"),
        ("total quantity", quantity_per_level * levels),
    ])

    responses: List[Dict[str, Any]] = []

    for i, p in enumerate(prices, 1):
        print(f"\n  ▶  Level {i}/{levels}  price={p}  qty={quantity_per_level} …", end=" ", flush=True)
        logger.info("Grid level %d/%d — price=%s qty=%s", i, levels, p, quantity_per_level)

        params: Dict[str, Any] = {
            "symbol":      symbol,
            "side":        side,
            "type":        "LIMIT",
            "quantity":    str(quantity_per_level),
            "price":       str(p),
            "timeInForce": time_in_force,
        }

        try:
            resp = client.place_order(**params)
            responses.append(resp)
            print(f"orderId={resp.get('orderId')}  status={resp.get('status')}")
            logger.info("Grid level %d placed — orderId=%s", i, resp.get("orderId"))
        except BinanceClientError as exc:
            logger.error("Grid level %d failed — %s", i, exc)
            print(f"FAILED ({exc})")
            responses.append({"error": str(exc), "level": i, "price": str(p)})

    placed = sum(1 for r in responses if "orderId" in r)
    print(f"\n✔  Grid complete — {placed}/{levels} levels placed successfully.")
    logger.info("Grid finished — %d/%d levels succeeded", placed, levels)
    return responses
