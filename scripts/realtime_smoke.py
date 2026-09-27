"""Realtime smoke test against the backend websocket endpoint."""
import asyncio
import json
import sys
import uuid
from urllib.request import Request, urlopen

API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/api/realtime/ws"


def login(username, password):
    req = Request(API_BASE + "/api/auth/login", data=json.dumps({"username": username, "password": password}).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def create_patient(token):
    payload = {
        "name": "Realtime Smoke Patient",
        "age": 44,
        "disease": "RealtimeTest",
        "diagnosis": "WS",
        "medicines": ["None"],
        "treatment_pattern": "Standard",
    }
    req = Request(API_BASE + "/api/patients", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}", "X-Session-Id": "realtime-smoke-1"}, method="POST")
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


async def run_test():
    import websockets

    admin = login("admin", "admin123")
    token = admin.get("access_token")
    if not token:
        print("ERROR: admin login failed")
        sys.exit(2)
    print("Admin login OK")

    async with websockets.connect(WS_URL) as ws:
        print("Connected to websocket")

        async def receiver():
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=15)
                print("Received websocket event:", msg)
                return msg
            except asyncio.TimeoutError:
                print("ERROR: timed out waiting for websocket event")
                return None

        task = asyncio.create_task(receiver())
        create_patient(token)
        result = await task
        if not result:
            sys.exit(2)
        parsed = json.loads(result)
        if parsed.get("type") != "patient_created":
            print("ERROR: unexpected event type", parsed)
            sys.exit(2)
        print("Realtime patient_created event OK")

if __name__ == '__main__':
    asyncio.run(run_test())
