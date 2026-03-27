"""
ui/server.py — Lightweight Flask web UI for the trading bot.

Run with:
    python ui/server.py

Then open http://localhost:5000 in your browser.
Credentials are passed via environment variables or the settings form in the UI.
"""

from __future__ import annotations

import os
import sys
import json
from decimal import Decimal
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request, session

# Make the parent package importable when run from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.credentials import load_credentials, save_credentials, clear_credentials, credentials_source
from bot.advanced_orders import (
    place_grid_order,
    place_oco_order,
    place_stop_limit_order,
    place_twap_order,
)
from bot.client import BinanceClient, BinanceClientError
from bot.orders import place_limit_order, place_market_order, place_stop_market_order
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

app = Flask(__name__, template_folder="templates")
app.secret_key = os.urandom(24)


def _get_client() -> BinanceClient:
    # Priority: session (user entered in UI) → saved file / env vars
    api_key    = session.get("api_key",    "").strip()
    api_secret = session.get("api_secret", "").strip()
    if not api_key or not api_secret:
        api_key, api_secret = load_credentials()
    if not api_key or not api_secret:
        raise ValueError("API credentials not configured. Use the Settings panel to save them.")
    return BinanceClient(api_key, api_secret)


def _ok(data: Any) -> Any:
    return jsonify({"status": "ok", "data": data})


def _err(msg: str, code: int = 400) -> Any:
    return jsonify({"status": "error", "message": msg}), code


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/credentials", methods=["GET"])
def get_credential_status():
    """Return current credential source (never returns the actual values)."""
    source = credentials_source()
    api_key, _ = load_credentials()
    return _ok({"source": source, "configured": bool(api_key)})


@app.route("/api/credentials", methods=["POST"])
def set_credentials():
    body      = request.get_json(force=True)
    api_key   = body.get("api_key",   "").strip()
    api_secret = body.get("api_secret", "").strip()
    persist   = body.get("save", False)

    session["api_key"]    = api_key
    session["api_secret"] = api_secret

    # Optionally persist to disk
    if persist and api_key and api_secret:
        save_credentials(api_key, api_secret)

    # Quick ping to validate
    try:
        client = _get_client()
        ts = client.get_server_time()
        return _ok({"server_time": ts, "saved": persist, "source": credentials_source()})
    except Exception as exc:
        return _err(str(exc))


@app.route("/api/credentials", methods=["DELETE"])
def delete_credentials():
    """Clear saved credentials from disk and session."""
    session.pop("api_key",    None)
    session.pop("api_secret", None)
    cleared = clear_credentials()
    return _ok({"cleared": cleared})


@app.route("/api/order", methods=["POST"])
def place_order():
    body = request.get_json(force=True)

    try:
        client     = _get_client()
        symbol     = validate_symbol(body.get("symbol", ""))
        side       = validate_side(body.get("side", ""))
        order_type = validate_order_type(body.get("order_type", ""))
        quantity   = validate_quantity(body.get("quantity", ""))
    except ValueError as exc:
        return _err(str(exc))

    try:
        resp: Any

        if order_type == "MARKET":
            resp = place_market_order(client, symbol, side, quantity)

        elif order_type == "LIMIT":
            price = validate_price(body.get("price"), order_type)
            tif   = body.get("time_in_force", "GTC").upper()
            resp  = place_limit_order(client, symbol, side, quantity, price, tif)

        elif order_type == "STOP_MARKET":
            stop_price = validate_stop_price(body.get("stop_price"), order_type)
            resp = place_stop_market_order(client, symbol, side, quantity, stop_price)

        elif order_type == "STOP_LIMIT":
            price      = validate_quantity(body.get("price", ""))
            stop_price = validate_quantity(body.get("stop_price", ""))
            tif        = body.get("time_in_force", "GTC").upper()
            resp = place_stop_limit_order(client, symbol, side, quantity, price, stop_price, tif)

        elif order_type == "OCO":
            tp_price  = validate_quantity(body.get("price", ""))
            stop_trig = validate_quantity(body.get("stop_price", ""))
            stop_lim  = validate_quantity(body.get("stop_limit_price", ""))
            resp = place_oco_order(client, symbol, side, quantity, tp_price, stop_trig, stop_lim)

        elif order_type == "TWAP":
            slices   = int(body.get("slices",   5))
            interval = int(body.get("interval", 10))
            ct       = body.get("child_type", "MARKET").upper()
            price    = validate_quantity(body.get("price")) if ct == "LIMIT" else None
            resp = place_twap_order(client, symbol, side, quantity, slices, interval, ct, price)

        elif order_type == "GRID":
            levels   = int(body.get("levels",    5))
            start    = validate_quantity(body.get("start_price",    ""))
            step     = validate_quantity(body.get("step",           ""))
            resp = place_grid_order(client, symbol, side, quantity, levels, start, step)

        else:
            return _err(f"Unsupported order type: {order_type}")

    except BinanceClientError as exc:
        return _err(f"Binance API error {exc.code}: {exc.message}")
    except ValueError as exc:
        return _err(str(exc))
    except Exception as exc:
        return _err(f"Unexpected error: {exc}", 500)

    # Serialise Decimal values
    def _serialise(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, list):
            return [_serialise(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _serialise(v) for k, v in obj.items()}
        return obj

    return _ok(_serialise(resp))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  ⬡  Trading Bot UI  →  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
