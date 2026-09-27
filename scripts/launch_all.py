import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
backend_dir = root_dir / "backend"
frontend_dir = root_dir / "frontend"
python_exe = root_dir / ".venv" / "Scripts" / "python.exe"
if not python_exe.exists():
    python_exe = sys.executable

print("[*] Launching Backend Server on port 8000...")
backend_proc = subprocess.Popen(
    [str(python_exe), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(backend_dir),
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

print("[*] Launching Admin Portal on port 5173...")
admin_proc = subprocess.Popen(
    "npx.cmd vite --port 5173 --host 127.0.0.1",
    cwd=str(frontend_dir),
    shell=True,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

print("[*] Launching Hacker Portal on port 5174...")
hacker_proc = subprocess.Popen(
    "npx.cmd vite --port 5174 --host 127.0.0.1",
    cwd=str(frontend_dir),
    shell=True,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

time.sleep(3)

def check_url(name, url):
    try:
        res = urllib.request.urlopen(url, timeout=3)
        print(f"[SUCCESS] {name} is accessible at {url} (HTTP {res.getcode()})")
        return True
    except Exception as e:
        print(f"[PENDING] {name} at {url} - {e}")
        return False

print("\n--- Service Health Status ---")
check_url("Backend API", "http://127.0.0.1:8000/health")
check_url("Admin Portal", "http://127.0.0.1:5173/")
check_url("Hacker Portal", "http://127.0.0.1:5174/")
