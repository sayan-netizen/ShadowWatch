from marshmallow import Schema, fields, validate, ValidationError
import re

def validate_password_strength(password):
    """
    Validates password strength:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("Password must contain at least one special character.")

class RegistrationSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate_password_strength)

class LoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

class AnalyzeURLSchema(Schema):
    url = fields.URL(required=True, schemes={'http', 'https'})


# ---------------------------------------------------------------------------
# Antigravity — Endpoint Module Schemas
# ---------------------------------------------------------------------------

class HostRegistrationSchema(Schema):
    """Validates a host registration request from the frontend / setup wizard."""
    hostname = fields.String(required=True, validate=validate.Length(min=1, max=255))
    os_info  = fields.String(load_default="unknown", validate=validate.Length(max=255))


class ProcessSchema(Schema):
    """Describes a single running process entry in a telemetry payload."""
    pid          = fields.Integer(required=True)
    name         = fields.String(required=True, validate=validate.Length(max=255))
    exe          = fields.String(load_default=None, allow_none=True)
    ppid         = fields.Integer(load_default=None, allow_none=True)
    cpu_percent  = fields.Float(load_default=0.0)
    mem_mb       = fields.Float(load_default=0.0)
    username     = fields.String(load_default=None, allow_none=True)
    status       = fields.String(load_default="unknown")


class MetricsSchema(Schema):
    """Aggregate system-level behavioral metrics."""
    disk_writes_per_second = fields.Float(load_default=0.0)
    hidden_file_events     = fields.Integer(load_default=0)
    net_connections_count  = fields.Integer(load_default=0)
    cpu_overall_percent    = fields.Float(load_default=0.0)
    memory_percent         = fields.Float(load_default=0.0)


class TelemetrySchema(Schema):
    """Top-level telemetry payload sent by the monitor.py agent."""
    processes  = fields.List(fields.Nested(ProcessSchema), load_default=[])
    metrics    = fields.Nested(MetricsSchema, load_default={})
    indicators = fields.List(fields.String(), load_default=[])
    agent_version = fields.String(load_default="1.0.0")

