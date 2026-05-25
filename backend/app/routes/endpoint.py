"""
endpoint.py — Antigravity Endpoint Monitoring API Routes

Integration:
- Registered under /api/endpoint/ prefix in app/__init__.py.
- Uses existing token_required for user-facing routes (dashboard operations).
- Uses new api_key_required for agent-facing routes (telemetry ingestion).
- All responses follow the existing success_response / error_response contract.
- Rate limiting reuses the existing Flask-Limiter instance.

Routes:
  POST /api/endpoint/register  — Register a host (JWT), returns one-time API key
  POST /api/endpoint/telemetry — Ingest agent telemetry (API Key)
  GET  /api/endpoint/alerts    — Dashboard: fetch endpoint alerts (JWT)
  GET  /api/endpoint/status    — Dashboard: host status summary (JWT)
  PUT  /api/endpoint/alerts/<id>/read — Mark alert read (JWT)
"""

from flask import Blueprint, request
from marshmallow import ValidationError

from app.utils.auth_middleware import token_required
from app.utils.api_key_auth import api_key_required
from app.utils.response import success_response, error_response
from app.utils.limiter import limiter
from app.utils.logger import log_security_event
from app.utils.db import get_db
from app.utils.validators import HostRegistrationSchema, TelemetrySchema
from app.services.endpoint_service import (
    register_host,
    ingest_telemetry,
    get_endpoint_alerts,
    get_endpoint_status,
    mark_alert_read,
)

endpoint_bp = Blueprint("endpoint", __name__)


# ---------------------------------------------------------------------------
# POST /api/endpoint/register
# Auth: JWT (user must be logged in)
# ---------------------------------------------------------------------------

@endpoint_bp.route("/register", methods=["POST"])
@limiter.limit("20 per hour")
@token_required
def register_endpoint(current_user):
    """
    Register a new monitored host under the authenticated user's account.
    Returns a one-time plaintext API key — store it securely on the agent side.
    Calling this again for the same hostname rotates the key.
    """
    try:
        data = HostRegistrationSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response("Validation error", "VALIDATION_ERROR", 400, err.messages)

    user_id = str(current_user["_id"])
    result  = register_host(user_id, data["hostname"], data.get("os_info", "unknown"))

    db = get_db()
    log_security_event(
        db, user_id,
        "endpoint_registered",
        f"Host '{data['hostname']}' registered",
        request.remote_addr
    )

    return success_response(
        {
            "host_id": result["host_id"],
            "api_key": result["api_key"],
            "warning": (
                "Store this API key securely. "
                "It will not be shown again. "
                "Re-register the same hostname to rotate the key."
            ),
        },
        "Host registered successfully",
        201,
    )


# ---------------------------------------------------------------------------
# POST /api/endpoint/telemetry
# Auth: API Key (X-API-Key header) — used by the headless monitor.py agent
# ---------------------------------------------------------------------------

@endpoint_bp.route("/telemetry", methods=["POST"])
@api_key_required
@limiter.limit("120 per minute")   # allow fast polling; 1 req/sec per agent
def ingest_endpoint_telemetry(host, user_id):
    """
    Receive a behavioral telemetry snapshot from the endpoint agent.
    Scores the payload, persists it, and optionally raises an endpoint alert.
    """
    try:
        data = TelemetrySchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response("Telemetry validation error", "VALIDATION_ERROR", 400, err.messages)

    threat = ingest_telemetry(host, user_id, data)

    return success_response(
        {
            "threat_level": threat["threat_level"],
            "raw_score":    threat["raw_score"],
            "rules_fired":  threat["rules_fired"],
        },
        f"Telemetry ingested — {threat['threat_level']}",
        200,
    )


# ---------------------------------------------------------------------------
# GET /api/endpoint/alerts
# Auth: JWT
# ---------------------------------------------------------------------------

@endpoint_bp.route("/alerts", methods=["GET"])
@token_required
@limiter.limit("60 per minute")
def get_alerts(current_user):
    """Return the most recent endpoint alerts for the authenticated user."""
    user_id = str(current_user["_id"])
    limit   = min(int(request.args.get("limit", 50)), 200)
    alerts  = get_endpoint_alerts(user_id, limit=limit)

    return success_response(
        {"alerts": alerts, "count": len(alerts)},
        "Endpoint alerts retrieved",
        200,
    )


# ---------------------------------------------------------------------------
# GET /api/endpoint/status
# Auth: JWT
# ---------------------------------------------------------------------------

@endpoint_bp.route("/status", methods=["GET"])
@token_required
@limiter.limit("60 per minute")
def get_status(current_user):
    """Return a summary of all monitored hosts and alert statistics."""
    user_id = str(current_user["_id"])
    status  = get_endpoint_status(user_id)

    return success_response(status, "Endpoint status retrieved", 200)


# ---------------------------------------------------------------------------
# PUT /api/endpoint/alerts/<alert_id>/read
# Auth: JWT
# ---------------------------------------------------------------------------

@endpoint_bp.route("/alerts/<alert_id>/read", methods=["PUT"])
@token_required
@limiter.limit("120 per minute")
def mark_endpoint_alert_read(current_user, alert_id):
    """Mark a single endpoint alert as read."""
    user_id = str(current_user["_id"])
    updated = mark_alert_read(user_id, alert_id)

    if not updated:
        return error_response("Alert not found or not owned by user.", "NOT_FOUND", 404)

    return success_response(None, "Alert marked as read", 200)
