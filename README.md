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

## Brevo OTP troubleshooting

If Brevo returns `401 unauthorized` with an unrecognized-IP error, authorize the blocked backend outbound IP in [Brevo Authorized IPs](https://app.brevo.com/security/authorised_ips) and verify that the configured sender is verified. Brevo applies authorized IPs to API and SMTP keys; do not disable IP blocking as a workaround.

For mobile OTPs, Brevo requires a registered and approved SMS Sender ID for each destination country and an SMS credit balance. Register the sender under [Brevo SMS Sender ID settings](https://app.brevo.com/sms-compliance/listing), then set its exact approved name in `BREVO_SMS_SENDER` in the backend environment and restart the backend. Sender IDs cannot be guessed or registered through the send-SMS API. After Brevo accepts a message, inspect its [transactional SMS logs](https://app-sms.sendinblue.com/log) to distinguish carrier delivery failures from application errors.

## Database Runbook

See [backend/DB_RUNBOOK.md](backend/DB_RUNBOOK.md) for local database initialization and Alembic upgrade steps.

## Google Patient Sign-In

Enable the Google provider in Firebase Authentication and add the local and production frontend domains to Firebase's authorized domains. Set `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, and `VITE_FIREBASE_APP_ID` for the frontend build (Vercel environment variables for Vercel, or build arguments for Docker Compose). The frontend prompts Google to select an account and sends its Firebase ID token to the backend; the backend accepts a Google-verified address only when it matches exactly one existing patient email.

The backend verifies Firebase ID token signatures, project audience, issuer, and expiry against `FIREBASE_PROJECT_ID` using Google's public signing certificates; Admin credentials are not required. For Docker Compose, put frontend build variables and backend settings in an untracked root `.env` file; local backend settings also read the root `.env.local`. Sign-in fails closed if Firebase configuration is missing or the verified email has no unique patient match. Firebase is used for Google patient sign-in; password-recovery OTPs are delivered through the configured email and SMS providers below.

Firebase Auth email verification links are sent by the `functions/emailVerification` Cloud Function. Select the Firebase project with `firebase use --add`, set the provider credentials as Firebase secrets (do not put them in the frontend or commit them), and deploy the function:

```powershell
firebase functions:secrets:set RESEND_API_KEY
firebase functions:secrets:set RESEND_FROM_ADDRESS
firebase deploy --only functions:emailVerification
```

Use a Resend API key and a sender address verified with Resend. The function accepts a POST request authenticated with the signed-in Firebase user's ID token, sends a Firebase-generated, single-use verification link to that user's email, and Firebase marks the account verified when the link is opened. Email verification requires a Firebase Auth user with an unverified email; Google sign-in emails are already verified. The frontend helper `requestFirebaseEmailVerification` in `frontend/src/firebase.ts` calls the deployed function. This Cloud Function is separate from backend OTP for password recovery/login; those flows can use Brevo, Resend, or SMTP configured in the backend environment.

The **Account Profile** contact-verification forms use the authenticated FastAPI API: email OTPs are sent via Brevo, Resend, or SMTP, and patient mobile OTPs via Brevo, Twilio, or MSG91. Both codes are short-lived and attempt-limited; contact details are saved only after successful verification. Challenges are held in process memory, so a backend restart invalidates pending codes; use a shared store for multiple workers or instances. This is separate from the Firebase email-action-link Cloud Function and from Firebase secret configuration. Email/SMS provider credentials must be configured for the backend before live delivery works.

For local OTP setup, if you do not already have a root `.env`, copy `.env.example` to `.env`; otherwise, add the provider entries to your existing `.env` without replacing its other settings. For Brevo email and SMS, set `BREVO_API_KEY`, `BREVO_EMAIL_SENDER` to a verified sender email, and `BREVO_SMS_SENDER` to a sender configured in Brevo; `BREVO_EMAIL_SENDER_NAME` is optional. Configure `OTP_SMS_PROVIDER=brevo` to route mobile OTPs through Brevo. Email OTP delivery prefers Brevo when its key and sender are configured, then Resend, then SMTP. Mobile OTP delivery uses only the explicitly selected provider. Existing SMS choices remain available: Twilio (`OTP_SMS_PROVIDER=twilio`, account SID, SMS-enabled sender number, and an auth token or API key pair) or MSG91 (`OTP_SMS_PROVIDER=msg91`, auth key, and configured template). `TWILIO_DEFAULT_COUNTRY_CODE` defaults to `91` for national-format numbers; E.164 numbers are accepted directly. The backend reports delivery/configuration failures without falling back to another SMS provider. If mobile delivery is not configured, patient recovery can use the registered email when email delivery is configured. Restart the backend after changing environment values; for Compose, run `docker compose up -d --force-recreate backend`. Keep `.env` private and never commit real credentials. Production deployments should configure these values as backend secrets.

For recovery email, configure Brevo (`BREVO_API_KEY` and a verified `BREVO_EMAIL_SENDER`), Resend (`RESEND_API_KEY` and a verified `RESEND_FROM_ADDRESS`), or SMTP credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_ADDRESS`). The backend tries configured providers in order (Brevo, Resend, then SMTP) and continues to the next provider if delivery fails. Configure at least one working provider; an invalid Brevo API key or unverified sender still requires correction in Brevo. Brevo's transactional SMS sender settings do not configure transactional email—verify the email sender in the email/senders area of Brevo. These values can also be added to the private root `.env` or deployment secret store. A `.env.example` with blank entries is provided as a template.

To require email OTP verification after password login, configure a working Brevo, Resend, or SMTP email provider and set `LOGIN_EMAIL_OTP_ENABLED=true` in the backend environment. The backend sends the code only to the account's registered email address; the login screen displays a masked destination and accepts the code in a second step. The code expires after five minutes, permits at most five attempts, and is single-use. Challenges are held in process memory, so a backend restart invalidates pending codes; use a shared store if deploying multiple backend workers or instances. Google sign-in continues to rely on Google's verified identity. Set this variable in the Compose environment or deployment secrets as well; login fails closed if OTP delivery is required but the provider or registered email is unavailable.

After Google patient sign-in, the account profile automatically shows the verified Google email. Google sign-in does not expose a user's mobile number through the normal email/profile scopes, so the patient enters a number in **Account Profile** and verifies ownership with an SMS code. The backend stores the number only after successful verification, prevents linking a number already assigned to another account, expires codes after five minutes, limits attempts, and throttles resends. Configure Brevo (`OTP_SMS_PROVIDER=brevo`, `BREVO_API_KEY`, and `BREVO_SMS_SENDER`), Twilio, or MSG91 before using phone verification. SMS challenges are kept in process memory and are invalidated on backend restart; use a shared store for multiple workers or instances.

Password recovery email can use Brevo (`BREVO_API_KEY` and `BREVO_EMAIL_SENDER`), Resend (`RESEND_API_KEY` and a provider-verified `RESEND_FROM_ADDRESS`), or SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and optionally `SMTP_FROM_ADDRESS`); the older SMTP names `SMTP_USER`, `SMTP_PASS`, and `SMTP_FROM` remain supported. Brevo is preferred when its key and sender are configured, then Resend, then SMTP. Select Brevo, Twilio, or MSG91 for SMS using `OTP_SMS_PROVIDER`; Brevo requires `BREVO_API_KEY` and a configured `BREVO_SMS_SENDER`, Twilio uses the official Python SDK with `TWILIO_ACCOUNT_SID`, an SMS-enabled `TWILIO_FROM_NUMBER`, and either `TWILIO_AUTH_TOKEN` or the API key pair `TWILIO_API_KEY_SID` and `TWILIO_API_KEY_SECRET`, and MSG91 requires `MSG91_AUTH_KEY` and a configured `MSG91_TEMPLATE_ID`. API key authentication is preferred for Twilio when both API key settings are present. Store these values in an untracked private environment file or deployment secret store; never commit credentials or paste them into chat. If credentials have been exposed, revoke/rotate them at the provider before use. `TWILIO_DEFAULT_COUNTRY_CODE` defaults to `91` for national-format mobile numbers; use E.164 numbers for other regions. Set `ADMIN_RECOVERY_EMAIL` and `ADMIN_RECOVERY_PHONE` to the administrator's verified contacts in the backend environment; these settings update the seeded admin account on backend startup. The administrator can enter a new email address, mobile number, or both during recovery. The backend sends one code to the registered account email and an additional code to each new contact; all codes are required to reset the password. Administrator recovery requires a configured email provider and, when a mobile number is used, the selected SMS provider. Patients can recover through the mobile number used at registration, even when an older patient record predates the `phone_number` column; if SMS delivery is unavailable, the registered email can be used as a fallback when an email provider is configured. OTPs expire after five minutes, are not returned by the API, and can only be used once. Existing administrator passwords are retained across backend restarts so password resets persist.

If both delivery channels are unavailable, an operator with authorized access to the backend host can reset an administrator password interactively without changing recovery contacts: run `docker compose exec -it backend python -m app.reset_admin_password admin` for Compose, or from the `backend` directory run `python -m app.reset_admin_password admin` locally. The command confirms the target username, prompts for the new password without echoing it, requires an interactive terminal, and writes an audit event. It does not configure SMS/email delivery; configure the selected SMS provider and an email provider separately to restore self-service recovery.

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
