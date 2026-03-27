# Binance Futures Testnet Trading Bot

A clean, structured Python CLI application for placing orders on the [Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com).

---

## Features

| Capability | Details |
|---|---|
| Order types | **MARKET**, **LIMIT**, **STOP_MARKET** (bonus) |
| Sides | BUY and SELL |
| Input | `argparse` CLI with full validation |
| Output | Formatted request summary + response table |
| Logging | Structured file logs (DEBUG) + console (INFO) |
| Error handling | API errors, network failures, invalid input |
| Architecture | Layered: `client` → `orders` → `cli` |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, retries, logging)
│   ├── orders.py          # Order placement logic + formatted output
│   ├── validators.py      # Input validation (raises ValueError on failure)
│   └── logging_config.py  # Shared logger factory
├── cli.py                 # CLI entry point (argparse)
├── logs/                  # Auto-created; log files written here
│   ├── sample_market_order_20250115.log
│   └── sample_limit_order_20250115.log
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com).
2. Log in (GitHub OAuth is supported).
3. Navigate to **API Management** → generate a new key pair.
4. Copy your **API Key** and **Secret Key** — the secret is shown only once.

### 2. Install Dependencies

```bash
# Python 3.8+ required
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Credentials

Either pass them as CLI flags on every call, or export them as environment variables (recommended):

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

On Windows (PowerShell):
```powershell
$env:BINANCE_API_KEY="your_testnet_api_key"
$env:BINANCE_API_SECRET="your_testnet_api_secret"
```

---

## How to Run

### General syntax

```
python cli.py [--api-key KEY] [--api-secret SECRET] \
              --symbol SYMBOL \
              --side {BUY,SELL} \
              --type {MARKET,LIMIT,STOP_MARKET} \
              --quantity QTY \
             [--price PRICE]           # required for LIMIT
             [--stop-price STOP_PRICE] # required for STOP_MARKET
             [--tif {GTC,IOC,FOK}]     # default GTC; LIMIT only
             [--log-dir DIR]           # default: logs/
```

### MARKET order — BUY

```bash
python cli.py \
  --symbol BTCUSDT \
  --side   BUY \
  --type   MARKET \
  --quantity 0.001
```

**Example output:**
```
====================================================
  ORDER REQUEST SUMMARY
====================================================
  symbol            : BTCUSDT
  side              : BUY
  type              : MARKET
  quantity          : 0.001
====================================================

====================================================
  ORDER RESPONSE
====================================================
  orderId           : 4751823946
  symbol            : BTCUSDT
  side              : BUY
  type              : MARKET
  status            : FILLED
  origQty           : 0.001
  executedQty       : 0.001
  avgPrice          : 96452.10000
====================================================

✔  Order placed successfully!
```

### LIMIT order — SELL

```bash
python cli.py \
  --symbol   BTCUSDT \
  --side     SELL \
  --type     LIMIT \
  --quantity 0.001 \
  --price    100000
```

### STOP_MARKET order — BUY (bonus)

```bash
python cli.py \
  --symbol     BTCUSDT \
  --side       BUY \
  --type       STOP_MARKET \
  --quantity   0.001 \
  --stop-price 95000
```

### Passing credentials inline (no env vars)

```bash
python cli.py \
  --api-key    "YOUR_KEY" \
  --api-secret "YOUR_SECRET" \
  --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Help

```bash
python cli.py --help
```

---

## Logging

Log files are written to the `logs/` directory (auto-created) with daily rotation:

```
logs/cli_YYYYMMDD.log
logs/binance_client_YYYYMMDD.log
logs/orders_YYYYMMDD.log
```

- **File handlers** capture DEBUG-level entries (full request params, raw response bodies).
- **Console handlers** show INFO-level entries only (clean, non-noisy output).

Sample log files for a MARKET and a LIMIT order are included in `logs/`.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing API credentials | Exit 1 with a descriptive message |
| Invalid symbol / side / type / qty / price | `ValueError` printed + logged; exit 1 |
| Price missing for LIMIT order | Validation error before any API call |
| Binance API error (e.g. bad precision) | `BinanceClientError` with code + message |
| Network timeout | Automatic retry (×3) via `urllib3.Retry`; then exit 1 |
| Unexpected exception | Full traceback logged to file; clean message to stderr |

---

## Assumptions

- All orders are placed on the **USDT-M Futures Testnet** (`https://testnet.binancefuture.com`).
- The bot does not manage positions, leverage, or margin — it places single orders only.
- `timeInForce` defaults to **GTC** for LIMIT orders; override with `--tif IOC` or `--tif FOK`.
- Quantity and price precision must be compatible with the symbol's exchange filters (Binance will return an error otherwise — the bot surfaces the API message clearly).
- No external config file is used; credentials are supplied via env vars or CLI flags.

---

## Requirements

```
requests>=2.31.0
urllib3>=2.0.0
```

Python 3.8 or later.

---

## Bonus Features

### All Three Bonus Items Implemented

---

### 1. Additional Order Types

| Type | Description |
|---|---|
| **STOP_LIMIT** | Limit fill triggered when market hits stop price |
| **OCO** | Take-profit + stop-loss pair; filling one cancels the other |
| **TWAP** | Splits large qty into N equal slices placed every X seconds |
| **GRID** | Ladder of LIMIT orders at evenly-spaced price levels |

---

### 2. Enhanced Interactive CLI (menu-driven)

Colour-coded, menu-driven terminal UI with step-by-step prompts and inline validation:

```bash
python interactive_cli.py
```

Features:
- Full-screen menu of all 7 order types
- Step-by-step field prompts with validation on every keystroke
- Confirmation screen before submission
- ANSI colour coding (green/red BUY/SELL, cyan accents, dim hints)
- Works with env vars OR credential prompts at startup

---

### 3. Lightweight Web UI

Flask-based single-page trading terminal:

```bash
pip install flask
python ui/server.py
# → open http://localhost:5000
```

Features:
- Left panel: click to switch order type — form updates instantly
- Middle panel: symbol, BUY/SELL toggle, quantity, dynamic fields per type
- Right panel: live activity log (status, orderId, avgPrice, errors)
- Settings drawer: enter API key + secret, test connection (shows server time)
- Industrial monospace aesthetic with scanline overlay + glow effects

---

### Running all three bonuses together

```
# Terminal 1 — original CLI
python cli.py --symbol BTCUSDT --side BUY --type GRID \
  --quantity 0.001 --start-price 94000 --step 500 --levels 5

# Terminal 2 — interactive menu CLI
python interactive_cli.py

# Terminal 3 — web UI
python ui/server.py
```
