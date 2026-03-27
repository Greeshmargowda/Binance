"""
bot/credentials.py — Persistent API credential storage.

Credentials are saved to ~/.trading_bot/credentials.json.
The secret is obfuscated with a machine-specific key (not true encryption,
but prevents casual shoulder-surfing of the file).  Users who need stronger
security should use environment variables instead.

Priority order when loading:
  1. Environment variables  (BINANCE_API_KEY / BINANCE_API_SECRET)
  2. Saved credentials file (~/.trading_bot/credentials.json)
  3. Not found → returns (None, None)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

# Config directory lives in the user's home folder, not the project dir
_CONFIG_DIR  = Path.home() / ".trading_bot"
_CONFIG_FILE = _CONFIG_DIR / "credentials.json"


# ---------------------------------------------------------------------------
# Machine-specific obfuscation key (not cryptographic — just avoids plaintext)
# ---------------------------------------------------------------------------

def _machine_key() -> bytes:
    """Derive a stable bytes key from a machine identifier."""
    node = str(uuid.getnode())          # MAC address as integer string
    home = str(Path.home())
    raw  = f"{node}:{home}:trading_bot_v1"
    return hashlib.sha256(raw.encode()).digest()


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _encode(plaintext: str) -> str:
    obfuscated = _xor(plaintext.encode(), _machine_key())
    return base64.b64encode(obfuscated).decode()


def _decode(encoded: str) -> str:
    obfuscated = base64.b64decode(encoded.encode())
    return _xor(obfuscated, _machine_key()).decode()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Load credentials using the priority chain:
      1. Environment variables
      2. Saved config file
      3. (None, None)
    """
    # 1. Env vars
    env_key    = os.environ.get("BINANCE_API_KEY",    "").strip()
    env_secret = os.environ.get("BINANCE_API_SECRET", "").strip()
    if env_key and env_secret:
        return env_key, env_secret

    # 2. Config file
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            key    = _decode(data["api_key"])
            secret = _decode(data["api_secret"])
            if key and secret:
                return key, secret
        except Exception:
            pass  # corrupt file → fall through

    return None, None


def save_credentials(api_key: str, api_secret: str) -> None:
    """
    Persist credentials to ~/.trading_bot/credentials.json.
    The directory is created with mode 700; the file with mode 600.
    """
    _CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)

    payload = {
        "api_key":    _encode(api_key.strip()),
        "api_secret": _encode(api_secret.strip()),
    }
    _CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _CONFIG_FILE.chmod(0o600)


def clear_credentials() -> bool:
    """Delete saved credentials. Returns True if a file was removed."""
    if _CONFIG_FILE.exists():
        _CONFIG_FILE.unlink()
        return True
    return False


def credentials_exist() -> bool:
    """Return True if saved (non-env) credentials are present on disk."""
    return _CONFIG_FILE.exists()


def credentials_source() -> str:
    """Return a human-readable string describing where credentials came from."""
    env_key    = os.environ.get("BINANCE_API_KEY",    "").strip()
    env_secret = os.environ.get("BINANCE_API_SECRET", "").strip()
    if env_key and env_secret:
        return "environment variables"
    if _CONFIG_FILE.exists():
        return f"saved config ({_CONFIG_FILE})"
    return "not configured"
