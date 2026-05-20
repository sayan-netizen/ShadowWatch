"""
endpoint_service.py — Antigravity Threat Scoring Engine & Database Operations

Architecture:
- All threat-scoring logic lives in this service layer, NOT in the route layer.
- Routes are thin: validate input → call service → return response.
- The score_telemetry() function returns a structured ThreatResult dict whose
  shape is the stable public contract. If we swap rule-based logic for an ML
  model later, only the internals of score_telemetry() change.

Threat Level Thresholds:
  0–19  → SAFE
  20–49 → SUSPICIOUS
  50+   → MALICIOUS

Performance:
- Scoring is pure Python arithmetic with no I/O — benchmarks at <1ms for 200 processes.
- DB operations are single inserts or indexed reads (no full-collection scans).
- Alert insertion is conditional (only on SUSPICIOUS/MALICIOUS) to minimise write amplification.
"""

import os
import secrets
import hashlib
import datetime
import logging
from typing import Any

from app.utils.db import get_db


# ---------------------------------------------------------------------------
# Threat Scoring Rules
# ---------------------------------------------------------------------------

# Suspicious filesystem paths (lowercase for case-insensitive match)
SUSPICIOUS_PATHS = [
    os.path.join(os.environ.get("TEMP", "c:\\temp"), "").lower(),
    os.path.join(os.environ.get("TMP",  "c:\\temp"), "").lower(),
    "\\appdata\\roaming\\",
    "\\appdata\\local\\temp\\",
    "/tmp/",
    "/var/tmp/",
]

# Known keylogger / spyware process names (lowercase)
KNOWN_BAD_NAMES = {
    "keylogger.exe", "perfectkeylogger.exe", "ardamax.exe", "spyrix.exe",
    "refog.exe", "actualspy.exe", "allinonekeylogger.exe", "revealer.exe",
    "elite_keylogger.exe", "klog.exe", "logkeymaster.exe", "pykeylogger.py",
}

# Keyword fragments that are high-signal (lowercase)
SUSPICIOUS_NAME_KEYWORDS = [
    "keylog", "hookdll", "spyware", "rdpwrap", "ratclient",
    "capture_key", "kbhook", "winspy",
]

# Point values for each rule
RULE_SCORES = {
    "known_bad_name":      50,
    "suspicious_keyword":  35,
    "suspicious_path":     40,
    "appdata_path":        20,
    "high_cpu":            15,
    "orphaned_process":    25,
    "rapid_disk_writes":   30,
    "hidden_file_creation": 35,
}

THRESHOLDS = {
    "SAFE":       (0,  19),
    "SUSPICIOUS": (20, 49),
    "MALICIOUS":  (50, 9999),
}


def _classify(score: int) -> str:
    """Map a numeric score to a threat level string."""
    if score >= 50:
        return "MALICIOUS"
    if score >= 20:
        return "SUSPICIOUS"
    return "SAFE"


def score_telemetry(telemetry_data: dict) -> dict:
    """
    Analyse a telemetry payload and return a structured ThreatResult.

    Returns:
        {
            "raw_score": int,
            "threat_level": "SAFE" | "SUSPICIOUS" | "MALICIOUS",
            "rules_fired": [str],     # human-readable rule names for transparency
            "flagged_processes": [str] # names of processes that triggered rules
        }

    This output contract is stable — an ML model can replace the summation
    logic later without changing the callers.
    """
    total_score = 0
    rules_fired: list[str] = []
    flagged_processes: list[str] = []

    processes = telemetry_data.get("processes", [])
    metrics   = telemetry_data.get("metrics", {})

    for proc in processes:
        name = (proc.get("name") or "").lower()
        exe  = (proc.get("exe")  or "").lower()
        cpu  = proc.get("cpu_percent", 0.0)

        proc_flagged = False

        # Rule 1 — Known bad signature
        if name in KNOWN_BAD_NAMES:
            total_score += RULE_SCORES["known_bad_name"]
            rules_fired.append(f"known_bad_name:{name}")
            proc_flagged = True

        # Rule 2 — Suspicious keyword in name
        if not proc_flagged and any(kw in name for kw in SUSPICIOUS_NAME_KEYWORDS):
            total_score += RULE_SCORES["suspicious_keyword"]
            rules_fired.append(f"suspicious_keyword:{name}")
            proc_flagged = True

        # Rule 3 — Execution from temp / suspicious path
        if exe:
            if any(p in exe for p in SUSPICIOUS_PATHS):
                total_score += RULE_SCORES["suspicious_path"]
                rules_fired.append(f"suspicious_path:{exe}")
                proc_flagged = True
            elif "appdata" in exe:
                total_score += RULE_SCORES["appdata_path"]
                rules_fired.append(f"appdata_path:{exe}")
                proc_flagged = True

        # Rule 4 — Sustained high CPU
        if cpu > 80.0:
            total_score += RULE_SCORES["high_cpu"]
            rules_fired.append(f"high_cpu:{name}({cpu}%)")
            proc_flagged = True

        # Rule 5 — Orphaned process (no parent info supplied by agent)
        if proc.get("ppid") is None or proc.get("ppid") == 0:
            if name not in {"system", "idle", "[system process]", ""}:
                total_score += RULE_SCORES["orphaned_process"]
                rules_fired.append(f"orphaned_process:{name}")
                proc_flagged = True

        if proc_flagged:
            flagged_processes.append(name)

    # Rule 6 — Rapid disk writes (reported as aggregate metric)
    if metrics.get("disk_writes_per_second", 0) > 50:
        total_score += RULE_SCORES["rapid_disk_writes"]
        rules_fired.append("rapid_disk_writes")

    # Rule 7 — Hidden file creation events
    if metrics.get("hidden_file_events", 0) > 0:
        total_score += RULE_SCORES["hidden_file_creation"]
        rules_fired.append("hidden_file_creation")

    return {
        "raw_score":         total_score,
        "threat_level":      _classify(total_score),
        "rules_fired":       rules_fired,
        "flagged_processes": list(set(flagged_processes)),
    }


# ---------------------------------------------------------------------------
# API Key Management
# ---------------------------------------------------------------------------

def generate_api_key() -> tuple[str, str]:
    """
    Generate a cryptographically secure API key.
    Returns (raw_key, sha256_hash).
    The raw_key is shown ONCE to the user; only the hash is stored.
    """
    raw_key  = "ag-" + secrets.token_hex(32)   # 'ag-' prefix for easy identification
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, key_hash


# ---------------------------------------------------------------------------
# Host Registration
# ---------------------------------------------------------------------------

def register_host(user_id: str, hostname: str, os_info: str) -> dict:
    """
    Register a new monitored host for the given user.
    If the hostname is already registered under this user, regenerate the API key
    (key rotation) rather than creating a duplicate.

    Returns a dict with 'api_key' (plaintext, one-time) and 'host_id'.
    """
    db = get_db()
    raw_key, key_hash = generate_api_key()
    now = datetime.datetime.utcnow()

    existing = db.monitored_hosts.find_one({"user_id": user_id, "hostname": hostname})

    if existing:
        # Key rotation: update existing host record
        db.monitored_hosts.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "api_key_hash": key_hash,
                "os_info":      os_info,
                "last_seen":    now,
                "status":       "online",
            }}
        )
        host_id = str(existing["_id"])
        logging.info(f"[antigravity] API key rotated for host '{hostname}' (user: {user_id})")
    else:
        # New registration
        doc = {
            "user_id":      user_id,
            "hostname":     hostname,
            "os_info":      os_info,
            "api_key_hash": key_hash,
            "registered_at": now,
            "last_seen":    now,
            "status":       "online",
        }
        result = db.monitored_hosts.insert_one(doc)
        host_id = str(result.inserted_id)
        logging.info(f"[antigravity] New host registered: '{hostname}' (user: {user_id})")

    return {"api_key": raw_key, "host_id": host_id}


# ---------------------------------------------------------------------------
# Telemetry Ingestion
# ---------------------------------------------------------------------------

def ingest_telemetry(host: dict, user_id: str, payload: dict) -> dict:
    """
    Score incoming telemetry and persist it.
    Generates an endpoint_alert if threat level is SUSPICIOUS or MALICIOUS.

    Returns the scored ThreatResult enriched with the persisted document _id.
    """
    db      = get_db()
    host_id = str(host["_id"])
    now     = datetime.datetime.utcnow()

    threat  = score_telemetry(payload)

    telemetry_doc = {
        "host_id":          host_id,
        "user_id":          user_id,
        "hostname":         host.get("hostname", "unknown"),
        "processes":        payload.get("processes", []),
        "metrics":          payload.get("metrics", {}),
        "indicators":       payload.get("indicators", []),
        "raw_score":        threat["raw_score"],
        "threat_level":     threat["threat_level"],
        "rules_fired":      threat["rules_fired"],
        "flagged_processes": threat["flagged_processes"],
        "timestamp":        now,
    }

    result = db.endpoint_telemetry.insert_one(telemetry_doc)
    threat["telemetry_id"] = str(result.inserted_id)

    # Update host heartbeat
    db.monitored_hosts.update_one(
        {"_id": host["_id"]},
        {"$set": {"last_seen": now, "status": "online"}}
    )

    # Raise an alert for non-safe threat levels
    if threat["threat_level"] in ("SUSPICIOUS", "MALICIOUS"):
        flagged = ", ".join(threat["flagged_processes"]) or "unknown"
        alert_doc = {
            "host_id":      host_id,
            "user_id":      user_id,
            "hostname":     host.get("hostname", "unknown"),
            "message": (
                f"[{threat['threat_level']}] Endpoint '{host.get('hostname', 'unknown')}' "
                f"scored {threat['raw_score']}. Flagged: {flagged}."
            ),
            "threat_level": threat["threat_level"],
            "rules_fired":  threat["rules_fired"],
            "is_read":      False,
            "timestamp":    now,
        }
        db.endpoint_alerts.insert_one(alert_doc)
        logging.warning(
            f"[antigravity] {threat['threat_level']} alert for host '{host.get('hostname')}' "
            f"(score={threat['raw_score']})"
        )

    return threat


# ---------------------------------------------------------------------------
# Dashboard Query Helpers
# ---------------------------------------------------------------------------

def get_endpoint_alerts(user_id: str, limit: int = 50) -> list[dict]:
    """Fetch endpoint alerts for a user, newest first."""
    db     = get_db()
    alerts = list(
        db.endpoint_alerts
          .find({"user_id": user_id})
          .sort("timestamp", -1)
          .limit(limit)
    )
    for a in alerts:
        a["_id"]       = str(a["_id"])
        a["timestamp"] = a["timestamp"].isoformat() + "Z"
    return alerts


def get_endpoint_status(user_id: str) -> dict:
    """
    Return a summary of all monitored hosts for a user:
    - host list with last_seen and status
    - aggregate alert counts
    """
    db    = get_db()
    hosts = list(db.monitored_hosts.find({"user_id": user_id}))

    serialised = []
    for h in hosts:
        serialised.append({
            "host_id":       str(h["_id"]),
            "hostname":      h.get("hostname", "unknown"),
            "os_info":       h.get("os_info", ""),
            "status":        h.get("status", "unknown"),
            "last_seen":     h["last_seen"].isoformat() + "Z" if h.get("last_seen") else None,
            "registered_at": h["registered_at"].isoformat() + "Z" if h.get("registered_at") else None,
        })

    total_alerts     = db.endpoint_alerts.count_documents({"user_id": user_id})
    unread_alerts    = db.endpoint_alerts.count_documents({"user_id": user_id, "is_read": False})
    malicious_alerts = db.endpoint_alerts.count_documents({"user_id": user_id, "threat_level": "MALICIOUS"})

    return {
        "monitored_hosts":  serialised,
        "host_count":       len(serialised),
        "total_alerts":     total_alerts,
        "unread_alerts":    unread_alerts,
        "malicious_alerts": malicious_alerts,
    }


def mark_alert_read(user_id: str, alert_id: str) -> bool:
    """Mark a single endpoint alert as read. Returns True if found and updated."""
    from bson.objectid import ObjectId
    db = get_db()
    result = db.endpoint_alerts.update_one(
        {"_id": ObjectId(alert_id), "user_id": user_id},
        {"$set": {"is_read": True}}
    )
    return result.matched_count > 0
