"""Simple smoke test script for the backend API endpoints.
Uses only standard library modules so it runs in the repo venv.
"""
import atexit
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_BASE = "http://127.0.0.1:8000"


def _ensure_server_started() -> None:
    global _backend_process
    if _backend_process is not None:
        return

    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", str(backend_dir), "--host", "127.0.0.1", "--port", "8000"]
    _backend_process = subprocess.Popen(
        command,
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    atexit.register(_terminate_backend_process)

    for _ in range(30):
        code, _ = req("/health")
        if code == 200:
            return
        time.sleep(1)


def _terminate_backend_process() -> None:
    global _backend_process
    if _backend_process is None:
        return
    try:
        _backend_process.terminate()
        _backend_process.wait(timeout=5)
    except Exception:
        pass
    _backend_process = None


_backend_process = None


def req(path, method="GET", token=None, data=None, headers=None):
    _ensure_server_started()
    url = API_BASE + path
    body = None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    if token:
        h["Authorization"] = f"Bearer {token}"
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = Request(url, data=body, headers=h, method=method)
    try:
        with urlopen(req, timeout=10) as resp:
            content = resp.read()
            try:
                parsed = json.loads(content.decode("utf-8"))
            except Exception:
                parsed = content.decode("utf-8")
            return resp.getcode(), parsed
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            return e.code, body
        except Exception:
            return e.code, str(e)
    except URLError as e:
        return None, str(e)


def ensure(code, msg):
    if code != 200:
        print("ERROR:", msg, "-> status:", code)
        sys.exit(2)


print("Checking /health")
code, body = req("/health")
ensure(code, "/health did not return 200")
print("OK")

print("Checking /admin and /hacker static pages")
for p in ["/admin", "/hacker"]:
    code, body = req(p)
    ensure(code, f"{p} did not return 200")
print("OK")

print("Logging in admin")
code, body = req("/api/auth/login", method="POST", data={"username": "admin", "password": "admin123"})
ensure(code, "admin login failed")
admin_token = body.get("access_token") if isinstance(body, dict) else None
if not admin_token:
    print("ERROR: admin token missing", body)
    sys.exit(2)
print("Admin login OK")

print("Logging in hacker")
code, body = req("/api/auth/login", method="POST", data={"username": "hacker", "password": "hacker123"})
ensure(code, "hacker login failed")
hacker_token = body.get("access_token") if isinstance(body, dict) else None
if not hacker_token:
    print("ERROR: hacker token missing", body)
    sys.exit(2)
print("Hacker login OK")

print("Fetching admin dashboard via API")
code, body = req("/api/dashboard/admin", token=admin_token)
ensure(code, "admin dashboard API failed")
print("Admin dashboard OK: role=", body.get("role") if isinstance(body, dict) else type(body))

print("Fetching hacker dashboard via API")
code, body = req("/api/dashboard/hacker", token=hacker_token)
ensure(code, "hacker dashboard API failed")
print("Hacker dashboard OK: role=", body.get("role") if isinstance(body, dict) else type(body))

print("Creating a test patient (admin)")
patient_payload = {"name": "Smoke Test Patient", "age": 42, "disease": "Testitis", "diagnosis": "Test", "medicines": ["None"], "treatment_pattern": "Standard"}
code, body = req("/api/patients", method="POST", token=admin_token, data=patient_payload, headers={"X-Session-Id": "smoke-session-1"})
ensure(code, "create patient failed")
print("Patient created ok")

print("Executing a hacker attack mode")
attack_payload = {"session_id": "smoke-session-h1", "mode": "probe_api", "details": "smoke test"}
code, body = req("/api/security/hack-modes/execute", method="POST", token=hacker_token, data=attack_payload)
ensure(code, "hack mode execution failed")
print("Hack mode executed OK")

print("All smoke checks passed")
sys.exit(0)
