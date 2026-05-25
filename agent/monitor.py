#!/usr/bin/env python3
"""
monitor.py — ShadowWatch Endpoint Agent v1.0
=============================================

Standalone behavioral telemetry agent for PhishGuard's ShadowWatch module.

Usage:
    python monitor.py --server http://localhost:5000 --api-key ag-<your_key>

Features:
    - Lightweight psutil-based process enumeration
    - Behavioral indicator detection (suspicious paths, CPU, disk I/O, etc.)
    - Configurable polling interval (default: 30 seconds)
    - Automatic retry with exponential back-off on network failures
    - Structured JSON telemetry formatted to match TelemetrySchema

Constraints:
    - Purely observational — zero system modification
    - Python standard library + psutil + requests only
    - Stable monitoring loop that survives temporary network outages
    - Sub-1% CPU overhead target at the default 30-second poll interval

Security notes:
    - API key is passed via --api-key flag or SHADOWWATCH_API_KEY env variable
    - All traffic is sent to the backend over HTTP/HTTPS (use HTTPS in production)
    - No credentials or key material are written to disk by this script
"""

import argparse
import datetime
import logging
import os
import platform
import sys
import time

import psutil
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SERVER  = "http://localhost:5000"
DEFAULT_INTERVAL = 30          # seconds between telemetry polls
AGENT_VERSION   = "1.0.0"
MAX_PROCESSES   = 200          # cap process list to avoid huge payloads
RETRY_BASE      = 5            # base seconds for exponential back-off
RETRY_MAX       = 120          # cap back-off at 2 minutes

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("shadowwatch-agent")


# ---------------------------------------------------------------------------
# Behavioral Indicator Helpers
# ---------------------------------------------------------------------------

SUSPICIOUS_PATH_FRAGMENTS = [
    os.path.join(os.environ.get("TEMP", "C:\\Temp"), "").lower(),
    os.path.join(os.environ.get("TMP",  "C:\\Temp"), "").lower(),
    "\\appdata\\local\\temp\\",
    "/tmp/",
    "/var/tmp/",
]

SUSPICIOUS_NAME_KEYWORDS = [
    "keylog", "hookdll", "spyware", "rdpwrap", "ratclient",
    "capture_key", "kbhook", "winspy",
]

KNOWN_BAD_NAMES = {
    "keylogger.exe", "perfectkeylogger.exe", "ardamax.exe", "spyrix.exe",
    "refog.exe", "actualspy.exe", "allinonekeylogger.exe", "revealer.exe",
    "elite_keylogger.exe", "klog.exe", "pykeylogger.py",
}


def collect_processes() -> list[dict]:
    """
    Enumerate running processes and return a sanitised list.
    Uses psutil's oneshot() context manager to batch attribute reads for
    performance (one kernel call per process instead of one per attribute).
    Caps output at MAX_PROCESSES to bound payload size.
    """
    results: list[dict] = []

    for proc in psutil.process_iter():
        try:
            with proc.oneshot():
                entry = {
                    "pid":         proc.pid,
                    "name":        proc.name(),
                    "exe":         None,
                    "ppid":        proc.ppid(),
                    "cpu_percent": round(proc.cpu_percent(interval=None), 2),
                    "mem_mb":      round(proc.memory_info().rss / (1024 * 1024), 2),
                    "username":    None,
                    "status":      proc.status(),
                }
                try:
                    entry["exe"] = proc.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                try:
                    entry["username"] = proc.username()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

            results.append(entry)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

        if len(results) >= MAX_PROCESSES:
            break

    return results


def collect_indicators(processes: list[dict]) -> list[str]:
    """
    Derive human-readable behavioral indicator strings from the process list.
    These are surfaced in the dashboard results panel.
    """
    indicators: list[str] = []
    for proc in processes:
        name = (proc.get("name") or "").lower()
        exe  = (proc.get("exe")  or "").lower()

        if name in KNOWN_BAD_NAMES:
            indicators.append(f"Known keylogger process: {proc['name']} (PID {proc['pid']})")
        elif any(kw in name for kw in SUSPICIOUS_NAME_KEYWORDS):
            indicators.append(f"Suspicious process name: {proc['name']} (PID {proc['pid']})")
        elif exe and any(p in exe for p in SUSPICIOUS_PATH_FRAGMENTS):
            indicators.append(f"Process running from temp path: {proc['name']} ({proc.get('exe','')})")

    if not indicators:
        indicators.append("No suspicious processes detected.")
    return indicators


def collect_metrics() -> dict:
    """Gather aggregate system-level metrics for the MetricsSchema."""
    disk_io = psutil.disk_io_counters()
    net_io  = psutil.net_connections()

    # Disk write rate — simplified: total writes / uptime gives avg writes/sec
    # For a proper rate, you'd diff two readings 1s apart; this is lightweight.
    disk_writes_per_second = 0.0
    if disk_io:
        uptime = time.time() - psutil.boot_time()
        disk_writes_per_second = round(disk_io.write_count / max(uptime, 1), 2)

    return {
        "disk_writes_per_second": disk_writes_per_second,
        "hidden_file_events":     0,          # requires FS watcher — future enhancement
        "net_connections_count":  len(net_io),
        "cpu_overall_percent":    round(psutil.cpu_percent(interval=1), 2),
        "memory_percent":         round(psutil.virtual_memory().percent, 2),
    }


# ---------------------------------------------------------------------------
# Telemetry Payload Builder
# ---------------------------------------------------------------------------

def build_payload() -> dict:
    """Build a complete telemetry payload ready to POST to /api/endpoint/telemetry."""
    processes  = collect_processes()
    indicators = collect_indicators(processes)
    metrics    = collect_metrics()

    return {
        "processes":     processes,
        "indicators":    indicators,
        "metrics":       metrics,
        "agent_version": AGENT_VERSION,
    }


# ---------------------------------------------------------------------------
# HTTP Client
# ---------------------------------------------------------------------------

def post_telemetry(server: str, api_key: str, payload: dict, retry: int = 0) -> bool:
    """
    POST the telemetry payload to the backend.
    Returns True on success, False on failure.
    Implements exponential back-off up to RETRY_MAX seconds.
    """
    url     = f"{server.rstrip('/')}/api/endpoint/telemetry"
    headers = {
        "X-API-Key":    api_key,
        "Content-Type": "application/json",
        "User-Agent":   f"ShadowWatchAgent/{AGENT_VERSION}",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15,
                             allow_redirects=False)  # Prevent HTTP→HTTPS redirect that silently drops POST body

        # Detect redirect — almost always an HTTP→HTTPS misconfiguration
        if resp.is_redirect or resp.status_code in (301, 302, 307, 308):
            location = resp.headers.get("Location", "?")
            log.warning(
                f"Server redirected (HTTP {resp.status_code}) to {location!r}. "
                f"Update --server to use HTTPS to avoid losing the POST body."
            )
            return False

        # Safe body read — empty body returns '' and never raises
        try:
            body = resp.text
        except Exception:
            body = ""

        # Guard: Render free-tier returns empty 502/503 during cold-start wake-up
        if not body.strip():
            log.warning(
                f"Server returned HTTP {resp.status_code} with an empty body. "
                f"Likely a cold-start on Render's free tier — will retry."
            )
            return False

        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception as json_err:
                log.error(
                    f"Backend returned HTTP 200 but body is not valid JSON "
                    f"({json_err}). Raw response: {body[:400]!r}"
                )
                return False
            level = data.get("data", {}).get("threat_level", "UNKNOWN")
            score = data.get("data", {}).get("raw_score", 0)
            log.info(f"Telemetry accepted — threat_level={level}, score={score}")
            return True

        elif resp.status_code in (401, 403):
            log.error(f"Authentication error ({resp.status_code}): {body[:200]!r}. Check your API key. Agent stopping.")
            sys.exit(1)   # Fatal — don't retry auth failures

        else:
            log.warning(f"Backend returned HTTP {resp.status_code}: {body[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        log.warning(f"Cannot reach {url} — server may be down. Will retry.")
        return False

    except requests.exceptions.Timeout:
        log.warning("Request timed out. Will retry.")
        return False

    except Exception as exc:
        log.error(f"Unexpected error posting telemetry: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main Monitoring Loop
# ---------------------------------------------------------------------------

def run_monitor(server: str, api_key: str, interval: int) -> None:
    """
    Stable polling loop. On network failure, retries with exponential back-off
    rather than crashing the process.
    """
    hostname = platform.node()
    log.info(f"ShadowWatch Agent v{AGENT_VERSION} starting")
    log.info(f"Host: {hostname} | Server: {server} | Poll interval: {interval}s")
    log.info("Press Ctrl+C to stop.")

    consecutive_failures = 0

    while True:
        try:
            log.debug("Collecting telemetry snapshot...")
            payload = build_payload()

            success = post_telemetry(server, api_key, payload)

            if success:
                consecutive_failures = 0
                time.sleep(interval)
            else:
                consecutive_failures += 1
                back_off = min(RETRY_BASE * (2 ** (consecutive_failures - 1)), RETRY_MAX)
                log.warning(f"Retry #{consecutive_failures} — waiting {back_off}s before next attempt.")
                time.sleep(back_off)

        except KeyboardInterrupt:
            log.info("Agent stopped by user.")
            break

        except Exception as exc:
            log.exception(f"Unhandled exception in monitoring loop: {exc}")
            time.sleep(RETRY_BASE)   # brief pause before continuing


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ShadowWatch Endpoint Agent — PhishGuard behavioral telemetry collector"
    )
    parser.add_argument(
        "--server",
        default=os.environ.get("SHADOWWATCH_SERVER", os.environ.get("ANTIGRAVITY_SERVER", DEFAULT_SERVER)),
        help=f"Backend server URL (default: {DEFAULT_SERVER})",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("SHADOWWATCH_API_KEY", os.environ.get("ANTIGRAVITY_API_KEY", "")),
        help="API key obtained from /api/endpoint/register (or SHADOWWATCH_API_KEY env var)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.environ.get("SHADOWWATCH_INTERVAL", os.environ.get("ANTIGRAVITY_INTERVAL", DEFAULT_INTERVAL))),
        help=f"Poll interval in seconds (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.api_key:
        log.error(
            "No API key provided. Pass --api-key <key> or set SHADOWWATCH_API_KEY env variable.\n"
            "Obtain a key by calling POST /api/endpoint/register with your JWT."
        )
        sys.exit(1)

    run_monitor(args.server, args.api_key, args.interval)
