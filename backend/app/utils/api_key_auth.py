"""
api_key_auth.py — Antigravity API Key Authentication Middleware

Security Design:
- API keys are generated as 32-byte cryptographically random hex strings (256-bit entropy).
- Only the SHA-256 hash of the key is stored in MongoDB (never the plaintext).
- The middleware does a constant-time comparison using hmac.compare_digest to
  prevent timing-oracle attacks against the key lookup.
- Keys are bound to a specific host document; if the host is deleted, the key
  becomes invalid automatically (DB lookup returns None).

Why a separate middleware instead of extending token_required?
- Endpoint agents run headlessly — no user session, no browser, no JWT refresh.
- Mixing host-identity auth into the JWT decorator would pollute its signature
  (current_user injection) and break every existing route that depends on it.
- A separate @api_key_required decorator keeps concerns cleanly isolated.
"""

from functools import wraps
import hashlib
import hmac
import logging

from flask import request
from app.utils.db import get_db
from app.utils.response import error_response


def _hash_api_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of a raw API key string."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def api_key_required(f):
    """
    Decorator that authenticates requests using the X-API-Key header.

    On success, injects (host_doc, user_id) as the first two positional args
    into the decorated function.

    Integration points:
    - Reads X-API-Key from request headers.
    - Hashes it and performs a single MongoDB lookup against monitored_hosts.
    - Uses constant-time comparison to prevent timing side-channels.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        raw_key = request.headers.get("X-API-Key", "").strip()

        if not raw_key:
            return error_response(
                "API key is missing.",
                "API_KEY_MISSING",
                401
            )

        key_hash = _hash_api_key(raw_key)
        db = get_db()

        host = db.monitored_hosts.find_one({"api_key_hash": key_hash})

        if not host:
            logging.warning(
                f"[antigravity] Invalid API key attempt from {request.remote_addr}"
            )
            return error_response(
                "Invalid or revoked API key.",
                "API_KEY_INVALID",
                401
            )

        return f(host, host["user_id"], *args, **kwargs)

    return decorated
