"""
Quick integration test for the Antigravity /api/endpoint/* routes.
Run from: backend/ directory
"""
import requests
import json
import sys

BASE = "http://127.0.0.1:5000"
PASS = "[PASS]"
FAIL = "[FAIL]"

def check(label, condition, detail=""):
    icon = PASS if condition else FAIL
    print(f"  {icon}  {label}" + (f" -- {detail}" if detail else ""))
    return condition

errors = 0

print("\n=== 1. Health Check ===")
r = requests.get(f"{BASE}/api/health")
if not check("GET /api/health -> 200", r.status_code == 200, r.json().get("status")):
    errors += 1

print("\n=== 2. Login (existing route -- regression check) ===")
r = requests.post(f"{BASE}/api/auth/login", json={"username": "testuser", "password": "Test1234!"})
if not check("POST /api/auth/login -> 200", r.status_code == 200):
    print(f"     Response: {r.text[:200]}")
    errors += 1
    print("FATAL: Cannot continue without a valid token.")
    sys.exit(1)

data  = r.json()
token = data["data"]["token"]
jwt_headers = {"Authorization": f"Bearer {token}"}
print(f"     Token: {token[:30]}...")

print("\n=== 3. Register Endpoint Host ===")
r = requests.post(
    f"{BASE}/api/endpoint/register",
    json={"hostname": "test-workstation-01", "os_info": "Windows 11 22H2"},
    headers=jwt_headers
)
check("POST /api/endpoint/register -> 201", r.status_code == 201, r.json().get("message"))
if r.status_code != 201:
    print(f"     Response: {r.text[:400]}")
    errors += 1

api_key = r.json().get("data", {}).get("api_key", "")
host_id = r.json().get("data", {}).get("host_id", "")
check("  Got api_key", api_key.startswith("ag-"), api_key[:20] + "...")
check("  Got host_id", bool(host_id), host_id)

print("\n=== 4. Post Telemetry (API Key auth) ===")
telemetry_payload = {
    "processes": [
        {"pid": 9999, "name": "chrome.exe", "exe": "C:\\Program Files\\Google\\Chrome\\chrome.exe",
         "ppid": 1000, "cpu_percent": 2.1, "mem_mb": 150.0, "status": "running"},
        {"pid": 8888, "name": "explorer.exe", "exe": "C:\\Windows\\explorer.exe",
         "ppid": 4, "cpu_percent": 0.5, "mem_mb": 80.0, "status": "running"},
    ],
    "metrics": {
        "disk_writes_per_second": 5.0,
        "hidden_file_events": 0,
        "net_connections_count": 12,
        "cpu_overall_percent": 15.0,
        "memory_percent": 42.0,
    },
    "indicators": [],
    "agent_version": "1.0.0",
}
r = requests.post(
    f"{BASE}/api/endpoint/telemetry",
    json=telemetry_payload,
    headers={"X-API-Key": api_key, "Content-Type": "application/json"}
)
check("POST /api/endpoint/telemetry -> 200", r.status_code == 200, r.json().get("message"))
if r.status_code == 200:
    d = r.json()["data"]
    check("  threat_level field present", "threat_level" in d, d.get("threat_level"))
    check("  raw_score field present", "raw_score" in d, str(d.get("raw_score")))
else:
    print(f"     Response: {r.text[:400]}")
    errors += 1

print("\n=== 5. Telemetry with MALICIOUS payload ===")
suspicious_payload = {
    "processes": [
        {"pid": 1234, "name": "keylogger.exe",
         "exe": "C:\\Users\\victim\\AppData\\Local\\Temp\\keylogger.exe",
         "ppid": None, "cpu_percent": 85.0, "mem_mb": 20.0, "status": "running"},
    ],
    "metrics": {"disk_writes_per_second": 60.0, "hidden_file_events": 2,
                "net_connections_count": 3, "cpu_overall_percent": 90.0, "memory_percent": 35.0},
    "indicators": [],
    "agent_version": "1.0.0",
}
r = requests.post(
    f"{BASE}/api/endpoint/telemetry",
    json=suspicious_payload,
    headers={"X-API-Key": api_key}
)
check("POST suspicious telemetry -> 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()["data"]
    check("  Detected as MALICIOUS", d.get("threat_level") == "MALICIOUS", d.get("threat_level"))
    check("  rules_fired populated", len(d.get("rules_fired", [])) > 0, str(d.get("rules_fired")))
else:
    print(f"     Response: {r.text[:400]}")
    errors += 1

print("\n=== 6. GET /api/endpoint/alerts ===")
r = requests.get(f"{BASE}/api/endpoint/alerts", headers=jwt_headers)
check("GET /api/endpoint/alerts -> 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()["data"]
    check("  alerts array present", "alerts" in d)
    check("  At least one alert generated", d.get("count", 0) >= 1, f"count={d.get('count')}")
else:
    print(f"     Response: {r.text[:400]}")
    errors += 1

print("\n=== 7. GET /api/endpoint/status ===")
r = requests.get(f"{BASE}/api/endpoint/status", headers=jwt_headers)
check("GET /api/endpoint/status -> 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()["data"]
    check("  monitored_hosts present", "monitored_hosts" in d)
    check("  host_count >= 1", d.get("host_count", 0) >= 1, f"count={d.get('host_count')}")
else:
    print(f"     Response: {r.text[:400]}")
    errors += 1

print("\n=== 8. Invalid API Key (security check) ===")
r = requests.post(f"{BASE}/api/endpoint/telemetry",
                  json={}, headers={"X-API-Key": "ag-invalid-key-000"})
check("Rejects invalid API key -> 401", r.status_code == 401, r.json().get("error_code"))

print("\n=== 9. Existing routes regression check ===")
r = requests.get(f"{BASE}/api/dashboard/stats", headers=jwt_headers)
check("GET /api/dashboard/stats still works -> 200", r.status_code == 200)

r = requests.get(f"{BASE}/api/scans/history", headers=jwt_headers)
check("GET /api/scans/history still works -> 200", r.status_code == 200)

print(f"\n{'='*40}")
print(f"  {'ALL TESTS PASSED' if errors == 0 else f'FAILURES: {errors}'}")
print(f"{'='*40}\n")
sys.exit(0 if errors == 0 else 1)
