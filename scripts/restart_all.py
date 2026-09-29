import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
backend_dir = root_dir / "backend"
gateway_dir = root_dir / "gateway"
ai_engine_dir = root_dir / "ai-engine"
frontend_dir = root_dir / "frontend"
python_exe = root_dir / ".venv" / "Scripts" / "python.exe"

log_dir = root_dir / "logs"
log_dir.mkdir(exist_ok=True)

backend_log = open(log_dir / "backend.log", "a", encoding="utf-8")
gateway_log = open(log_dir / "gateway.log", "a", encoding="utf-8")
ai_engine_log = open(log_dir / "ai_engine.log", "a", encoding="utf-8")
frontend_log = open(log_dir / "frontend_3000.log", "a", encoding="utf-8")
admin_log = open(log_dir / "frontend_5173.log", "a", encoding="utf-8")
hacker_log = open(log_dir / "frontend_5174.log", "a", encoding="utf-8")

print("[1/3] Terminating any existing processes on ports 8000, 8001, 8002, 3000, 5173, 5174...")
try:
    netstat_out = subprocess.check_output("netstat -ano", shell=True).decode("utf-8", errors="ignore")
    pids = set()
    for line in netstat_out.splitlines():
        if "LISTENING" in line and any(port in line for port in [":8000", ":8001", ":8002", ":3000", ":5173", ":5174"]):
            parts = line.split()
            if parts:
                pids.add(parts[-1])
    for pid in pids:
        print(f"    - Killing PID {pid}")
        subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception as e:
    print(f"    - Cleanup warning: {e}")

time.sleep(1)

print("[2/3] Spawning persistent detached processes for all services...")
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

backend_proc = subprocess.Popen(
    [str(python_exe), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(backend_dir),
    stdout=backend_log,
    stderr=subprocess.STDOUT,
    creationflags=flags
)

gateway_proc = subprocess.Popen(
    [str(python_exe), "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8001"],
    cwd=str(gateway_dir),
    stdout=gateway_log,
    stderr=subprocess.STDOUT,
    creationflags=flags
)

ai_engine_proc = subprocess.Popen(
    [str(python_exe), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8002"],
    cwd=str(ai_engine_dir),
    stdout=ai_engine_log,
    stderr=subprocess.STDOUT,
    creationflags=flags
)

frontend_proc = subprocess.Popen(
    ["cmd.exe", "/c", "npx.cmd", "vite", "--port", "3000", "--host", "127.0.0.1"],
    cwd=str(frontend_dir),
    stdout=frontend_log,
    stderr=subprocess.STDOUT,
    creationflags=flags
)

admin_proc = subprocess.Popen(
    ["cmd.exe", "/c", "npm.cmd", "run", "dev", "--", "--port", "5173", "--host", "127.0.0.1"],
    cwd=str(frontend_dir),
    stdout=admin_log,
    stderr=subprocess.STDOUT,
    creationflags=flags
)

print("[3/3] Waiting for servers to initialize...")
time.sleep(6)

def check_url(name, url):
    for _ in range(10):
        try:
            req = urllib.request.urlopen(url, timeout=3)
            print(f" [OK] {name}: {url} (HTTP {req.getcode()})")
            return True
        except Exception:
            time.sleep(1)
    print(f" [ERR] {name}: {url} failed to respond")
    return False

print("\n--- Endpoint Verification ---")
check_url("Backend API & Portal", "http://127.0.0.1:8000/health")
check_url("Backend Frontend Root", "http://127.0.0.1:8000/")
check_url("AI Gateway", "http://127.0.0.1:8001/health")
check_url("AI Twin Engine", "http://127.0.0.1:8002/health")
check_url("Admin / Hospital Portal (5173)", "http://127.0.0.1:5173/")
