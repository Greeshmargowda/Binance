#!/usr/bin/env python3
"""
cli.py — Command-line entry point for the Binance Futures Testnet trading bot.

Credentials are loaded automatically from ~/.trading_bot/credentials.json
if previously saved.  You only need to pass --api-key / --api-secret once
(with --save to persist them).

Usage examples
--------------
# Save credentials once — never type them again:
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET --save

# From now on, no credentials needed:
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

# Override saved creds for one command (without overwriting them):
python cli.py --api-key OTHER_KEY --api-secret OTHER_SECRET --symbol BTCUSDT ...

# Clear saved credentials:
python cli.py --clear-credentials

# Show where credentials are coming from:
python cli.py --cred-status
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal

from bot.client import BinanceClient, BinanceClientError
from bot.credentials import (
    clear_credentials,
    credentials_source,
    load_credentials,
    save_credentials,
)
from bot.logging_config import setup_logger
from bot.orders import place_limit_order, place_market_order, place_stop_market_order
from bot.advanced_orders import (
    place_grid_order, place_oco_order,
    place_stop_limit_order, place_twap_order,
)
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    creds = parser.add_argument_group("credentials")
    creds.add_argument("--api-key",    default=None, help="Binance Testnet API key")
    creds.add_argument("--api-secret", default=None, help="Binance Testnet API secret")
    creds.add_argument("--save", action="store_true",
                       help="Persist --api-key/--api-secret to ~/.trading_bot/credentials.json")
    creds.add_argument("--clear-credentials", action="store_true",
                       help="Delete saved credentials and exit")
    creds.add_argument("--cred-status", action="store_true",
                       help="Print credential source and exit")

    order = parser.add_argument_group("order parameters")
    order.add_argument("--symbol")
    order.add_argument("--side")
    order.add_argument("--type", dest="order_type",
                       help="MARKET | LIMIT | STOP_MARKET | STOP_LIMIT | OCO | TWAP | GRID")
    order.add_argument("--quantity")
    order.add_argument("--price",            default=None)
    order.add_argument("--stop-price",       default=None, dest="stop_price")
    order.add_argument("--stop-limit-price", default=None, dest="stop_limit_price")
    order.add_argument("--tif",              default="GTC", dest="time_in_force")
    order.add_argument("--slices",           type=int, default=5)
    order.add_argument("--interval",         type=int, default=10)
    order.add_argument("--child-type",       default="MARKET", dest="child_type")
    order.add_argument("--levels",           type=int, default=5)
    order.add_argument("--start-price",      default=None, dest="start_price")
    order.add_argument("--step",             default=None)

    parser.add_argument("--log-dir", default="logs")
    return parser


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    logger = setup_logger("cli", log_dir=args.log_dir)

    # ── Utility commands ─────────────────────────────────────────────────────
    if args.clear_credentials:
        if clear_credentials():
            print("✔  Saved credentials deleted.")
        else:
            print("·  No saved credentials found.")
        sys.exit(0)

    if args.cred_status:
        print(f"·  Credentials source: {credentials_source()}")
        sys.exit(0)

    # ── Resolve credentials ──────────────────────────────────────────────────
    if args.api_key and args.api_secret:
        api_key, api_secret = args.api_key.strip(), args.api_secret.strip()
        if args.save:
            save_credentials(api_key, api_secret)
            print("✔  Credentials saved to ~/.trading_bot/credentials.json")
            logger.info("Credentials saved.")
    else:
        api_key, api_secret = load_credentials()

    if not api_key or not api_secret:
        print(
            "\n✗  No API credentials found.\n\n"
            "   Save them once with:\n"
            "     python cli.py --api-key KEY --api-secret SECRET --save\n\n"
            "   Or export environment variables:\n"
            "     export BINANCE_API_KEY=your_key\n"
            "     export BINANCE_API_SECRET=your_secret\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"·  Using credentials from: {credentials_source()}")
    logger.info("Credentials loaded from: %s", credentials_source())

    # ── Require order fields ─────────────────────────────────────────────────
    for field, flag in [("symbol","--symbol"),("side","--side"),
                         ("order_type","--type"),("quantity","--quantity")]:
        if not getattr(args, field, None):
            parser.error(f"{flag} is required")

    # ── Validate ─────────────────────────────────────────────────────────────
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity   = validate_quantity(args.quantity)
    except ValueError as exc:
        print(f"\n✗  {exc}", file=sys.stderr)
        sys.exit(1)

    client = BinanceClient(api_key=api_key, api_secret=api_secret, log_dir=args.log_dir)

    # ── Dispatch ─────────────────────────────────────────────────────────────
    try:
        if order_type == "MARKET":
            place_market_order(client, symbol, side, quantity)

        elif order_type == "LIMIT":
            p = validate_price(args.price, "LIMIT")
            place_limit_order(client, symbol, side, quantity, p, args.time_in_force.upper())

        elif order_type == "STOP_MARKET":
            sp = validate_stop_price(args.stop_price, "STOP_MARKET")
            place_stop_market_order(client, symbol, side, quantity, sp)

        elif order_type == "STOP_LIMIT":
            p  = validate_quantity(args.price or "")
            sp = validate_quantity(args.stop_price or "")
            place_stop_limit_order(client, symbol, side, quantity, p, sp, args.time_in_force.upper())

        elif order_type == "OCO":
            p   = validate_quantity(args.price or "")
            sp  = validate_quantity(args.stop_price or "")
            slp = validate_quantity(args.stop_limit_price or "")
            place_oco_order(client, symbol, side, quantity, p, sp, slp)

        elif order_type == "TWAP":
            child_price = validate_quantity(args.price) if args.price else None
            place_twap_order(client, symbol, side, quantity,
                             args.slices, args.interval, args.child_type.upper(), child_price)

        elif order_type == "GRID":
            start = validate_quantity(args.start_price or "")
            step  = validate_quantity(args.step or "")
            place_grid_order(client, symbol, side, quantity, args.levels, start, step)

    except BinanceClientError as exc:
        logger.error("Order failed: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        print(f"\n✗  {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
