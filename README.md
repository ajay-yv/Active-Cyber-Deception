# Active Cyber Deception: Securing Healthcare Data using AI-Generated Synthetic Twins

Monorepo scaffold for a healthcare cyber deception platform.

## Layout

- `frontend/` - React + TypeScript UI
- `backend/` - FastAPI application
- `gateway/` - AI Security Gateway logic
- `ai-engine/` - Synthetic twin generation and anomaly detection
- `docs/` - Architecture and threat-model notes
- `docker/` - Compose and container assets
- `tests/` - Cross-service tests

## Current status

This workspace currently contains the first implementation scaffold. The next step is wiring the backend API, gateway policy engine, and frontend dashboard routes.

## Database Runbook

See [backend/DB_RUNBOOK.md](backend/DB_RUNBOOK.md) for local database initialization and Alembic upgrade steps.

## Google Patient Sign-In

Enable the Google provider in Firebase Authentication and add the local and production frontend domains to Firebase's authorized domains. Set `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, and `VITE_FIREBASE_APP_ID` for the frontend build (Vercel environment variables for Vercel, or build arguments for Docker Compose). The frontend prompts Google to select an account and sends its Firebase ID token to the backend; the backend accepts any Google-verified address only when it matches exactly one existing patient email.

The backend verifies Firebase ID token signatures, project audience, issuer, and expiry against `FIREBASE_PROJECT_ID` using Google's public signing certificates; Admin credentials are not required. For Docker Compose, put frontend build variables and backend settings in an untracked root `.env` file; local backend settings also read the root `.env.local`. Sign-in fails closed if Firebase configuration is missing or the verified email has no unique patient match.

## Local Cyber-Range Simulator

The terminal simulator is development-only. For another laptop on the same private development LAN, start the backend bound to the LAN interface and use the host laptop's private IP. The seeded simulator account is `hacker` / `hacker123`; all other credentials used by the simulator are dummy values.

On the host laptop, find its private address with `ipconfig`, then start the backend from the repository root:

```text
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Allow inbound TCP port 8000 only on the private development network in Windows Firewall. Do not expose this port to the public internet.

```text
python tools/security_simulator.py --attack brute-force --target http://127.0.0.1:8000 --attempts 20
python tools/security_simulator.py --attack enumeration --target http://127.0.0.1:8000 --count 20
python tools/security_simulator.py --attack single-patient --patient-id P-01 --target http://127.0.0.1:8000
python tools/security_simulator.py --attack single-patient --patient-id P-01 --target http://192.168.1.25:8000 --allow-private-network
python tools/security_simulator.py --attack api-abuse --target http://127.0.0.1:8000 --requests 30
python tools/security_simulator.py --attack sql-injection --target http://127.0.0.1:8000
python tools/security_simulator.py --attack traversal --target http://127.0.0.1:8000
python tools/security_simulator.py --attack exfiltration --target http://127.0.0.1:8000 --records 10
python tools/security_simulator.py --attack credential-stuffing --target http://127.0.0.1:8000
python tools/security_simulator.py --attack session-abuse --target http://127.0.0.1:8000 --requests 10
```

The simulator enforces bounded request counts, a minimum interval, fixed test credentials, and loopback/private-network validation. Private-network targets require the explicit `--allow-private-network` flag. The SQL and traversal commands submit harmless markers; they never execute SQL, access filesystem paths, or execute shell commands. The Admin/User dashboard receives the defender alert through the authenticated realtime WebSocket. Simulation endpoints are disabled when `APP_ENV` is not `development`, `test`, or `testing`.
