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

Enable the Google provider in Firebase Authentication and add the local and production frontend domains to Firebase's authorized domains. Set `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, and `VITE_FIREBASE_APP_ID` for the frontend build (Vercel environment variables for Vercel, or build arguments for Docker Compose). The frontend prompts Google to select an account and sends its Firebase ID token to the backend; the backend accepts a Google-verified address only when it matches exactly one existing patient email.

The backend verifies Firebase ID token signatures, project audience, issuer, and expiry against `FIREBASE_PROJECT_ID` using Google's public signing certificates; Admin credentials are not required. For Docker Compose, put frontend build variables and backend settings in an untracked root `.env` file; local backend settings also read the root `.env.local`. Sign-in fails closed if Firebase configuration is missing or the verified email has no unique patient match.

For Vercel, deploy a separately hosted FastAPI backend with persistent patient data, then set the server-side `HOSPITAL_API_BASE_URL` environment variable to its HTTPS origin (for example, `https://api.example.org`) for every environment you use. The root `api/[...path].js` function proxies same-origin `/api/*` requests to that backend, so the browser does not need backend CORS access. Leave `VITE_API_BASE_URL` unset in Vercel so browser calls use this proxy. Configure `FIREBASE_PROJECT_ID` on the backend and the four `VITE_FIREBASE_*` variables for the Vercel frontend build, then redeploy both services. Do not point the production frontend at a developer's localhost or use an ephemeral serverless filesystem for patient records.

## Local Cyber-Range Simulator

The terminal simulator is development-only. For another laptop on the same private development LAN, start the backend bound to the LAN interface and use the host laptop's private IP. The seeded simulator account is `hacker` / `hacker123`; all other credentials used by the simulator are dummy values.

For Docker Compose, the frontend and backend host ports are bound to loopback; gateway, AI engine, databases, and Redis are available only to other Compose services. The backend allows credentialed CORS only from the local development origins configured by default. To use a different frontend origin, set `CORS_ALLOWED_ORIGINS` to a comma-separated list of exact origins (scheme, hostname, and optional port); wildcard origins are rejected.

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

Enumeration makes a bounded set of ID probes, then prints the verified synthetic twins returned by the same persisted catalog feed used by the Admin Dashboard. It does not substitute built-in demo fixtures. The simulator enforces bounded request counts, a minimum interval, fixed test credentials, and loopback/private-network validation. Private-network targets require the explicit `--allow-private-network` flag. The SQL and traversal commands submit harmless markers; they never execute SQL, access filesystem paths, or execute shell commands. The Admin/User dashboard receives the defender alert through the authenticated realtime WebSocket. Simulation endpoints are disabled by default outside `development`, `test`, and `testing`.

### Controlled HTTPS cloud demo (two laptops)

Use this only with a dedicated demo deployment and a DNS hostname you control. Do not use the public Vercel frontend URL as the simulator target unless it is explicitly your configured backend host; do not test an unrelated public website. Keep production on `APP_ENV=production`. On the dedicated demo backend only, configure:

```text
APP_ENV=demo
SIMULATION_DEMO_ENABLED=true
SIMULATION_ALLOWED_HOSTS=api.your-controlled-demo.example
```

`SIMULATION_ALLOWED_HOSTS` is a comma-separated list of exact hostnames (no scheme, port, wildcard, or path). The simulation endpoints additionally require HTTPS on the standard HTTPS port, an authenticated `hacker` or `administrator` account, and the host allowlist match. Use a separate, disposable database containing only synthetic demo records and provision the demo `hacker` account with the simulator's fixed demo credentials (`hacker` / `hacker123`). Do not copy production credentials, patient data, or databases into the demo.

Expose only HTTPS through the deployment's TLS reverse proxy; do not publish the application server port directly. Configure the proxy to preserve the approved host and HTTPS scheme, forward only trusted proxy headers, and restrict inbound traffic to the guide's/demo participants' source IPs or VPN. The backend's HTTPS host check depends on correct trusted proxy configuration. Point the demo frontend's API configuration at this backend and sign in to the Admin Dashboard on Laptop 1. Enable browser audio there and verify the Admin and Hacker dashboards are connected to the same demo backend.

On Laptop 2, clone/open this project, install the existing backend dependencies if needed, and run a harmless bounded marker simulation. Replace the example hostname only with the exact DNS name configured above:

```powershell
python tools/security_simulator.py --attack sql-injection --target https://api.your-controlled-demo.example --authorized-demo-host api.your-controlled-demo.example
```

The CLI refuses arbitrary public hosts, HTTP, nonstandard remote ports, target paths, and redirects. The marker is a harmless test string rather than an executable SQL injection. The expected response is only synthetic records from the Admin Dashboard's AI Synthetic Patient Decoy Catalog; the Admin Dashboard should show the alert and forensic details. Never increase simulator request limits or point it at a third-party service. Actual DNS/proxy/firewall configuration depends on the cloud host; do not start the demo until those controls and the exact hostname have been provisioned.

### Failed sign-in alerts

Failed sign-ins are recorded without storing the submitted password. The Admin Dashboard siren is triggered after **5 failed attempts in 5 minutes** for the same attempted username and source IP. This includes unknown usernames and incorrect passwords for existing accounts; both return the same generic login error. A single typo is logged but does not raise the brute-force siren. The detection window is stored in the security database and is independent of the client-provided session ID.

For a local demo, sign in to the Admin Dashboard, enable browser audio with a click, then run the bounded simulator:

```powershell
python tools/security_simulator.py --attack brute-force --target http://127.0.0.1:8000 --attempts 5
```

The demo uses invalid test passwords for the simulator account; passwords are not included in the Admin alert or stored in the failed-attempt counter. The client IP is taken from the network connection. If the backend is behind a reverse proxy, set `TRUSTED_PROXY_CIDRS` to the proxy's trusted IP address(es) or CIDR ranges before relying on `X-Forwarded-For`; arbitrary forwarded headers from clients are ignored.

SQL/traversal simulator output is read from the authenticated synthetic-patient endpoint, which returns persisted synthetic twins from the Admin Dashboard's **AI Synthetic Patient Decoy Catalog**. The simulator does not use catalog data returned by older marker endpoints or built-in demo fixtures. It prints each verified synthetic patient in a separate block, displays synthetic IDs as `P-<suffix>`, and omits watermark fingerprints and linked real-patient identifiers. If no persisted twins exist, it reports an empty catalog rather than substituting demo data.

### Port already in use (Windows)

If Uvicorn reports `WinError 10048` on a port, another process is already listening there. A successful `/health` response confirms only that a server is listening, not that it is running the current source. Do not stop an unidentified process. Start the current source on an unused port (the example uses 8011) in a new PowerShell window:

```powershell
cd C:\Users\ajayy\OneDrive\Desktop\EHR
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8011
```

In a second PowerShell window, confirm that instance is responding and send the simulator to the same port:

```powershell
Invoke-RestMethod http://127.0.0.1:8011/health
python tools/security_simulator.py --attack sql-injection --target http://127.0.0.1:8011
```

The Admin Dashboard and SQL/traversal marker endpoint both read the persisted synthetic catalog; the marker endpoint does not add a separate demo record. Refresh the Admin Dashboard after starting the current backend, then run the simulator against that same backend port to see the matching catalog. If port 8011 is also occupied, choose another unused local port for both commands. A dashboard-catalog fallback can show decoys served by an older backend, but the Admin siren and detailed realtime alert require the current backend source and the Admin Dashboard to be connected to that same backend. Enable audio with a click in the Admin Dashboard browser before the demo attack.

For a UI demo, open the Admin Dashboard and enable siren audio in that browser before submitting a request from the Hacker Simulation dashboard. The admin forensic table records the request type, requested data fields, source IP, timestamp, threat score, and deception decision. Hacker requests are routed to synthetic records; linked patients can view only their own original record, while authorized doctors and administrators can view original records.
