from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.integration import router as integration_router
from app.api.realtime import router as realtime_router
from app.api.routes import router as api_router
from app.api.security import router as security_router
from app.api.security_extra import router as security_extra_router
from app.api.patients import router as patients_router
from app.api.audit import router as audit_router
from app.api.analytics import router as analytics_router
from app.db.bootstrap import create_all_tables

app = FastAPI(title="Healthcare Cyber Deception Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(api_router, prefix="/api")
app.include_router(patients_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.include_router(security_extra_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(integration_router, prefix="/api")
app.include_router(realtime_router, prefix="/api")
app.include_router(audit_router, prefix="/api")

create_all_tables()
 
@app.on_event("startup")
async def startup_event():
    import asyncio
    from app.services.realtime import manager
    try:
        manager.loop = asyncio.get_running_loop()
    except Exception:
        pass


@app.middleware("http")
async def gateway_middleware(request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    from app.core.security import decode_token
    from app.services.gateway import evaluate_request

    headers = request.headers
    session_id = headers.get("x-session-id") or f"anonymous-{uuid4().hex[:8]}"
    context = {
        "session_id": session_id,
        "device": headers.get("x-device", "trusted"),
        "browser": headers.get("x-browser", "chrome"),
        "operating_system": headers.get("x-os", "windows"),
        "ip_address": headers.get("x-forwarded-for", request.client.host if request.client else "0.0.0.0"),
        "country": headers.get("x-country", "unknown"),
    }

    username = None
    role = headers.get("x-role")
    auth = headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
        try:
            payload = decode_token(token)
            username = str(payload.get("sub", ""))
            role = role or str(payload.get("role", "anonymous"))
        except Exception:
            username = None
            role = role or "anonymous"

    body = None
    try:
        body_bytes = await request.body()
        body = body_bytes.decode("utf-8", errors="ignore") if body_bytes else None
    except Exception:
        body = None

    try:
        decision = evaluate_request(
            role=role or "anonymous",
            session_id=context["session_id"],
            device=context["device"],
            browser=context["browser"],
            operating_system=context["operating_system"],
            ip_address=context["ip_address"],
            country=context["country"],
            username=username,
            method=request.method,
            path=request.url.path,
            params=dict(request.query_params),
            body=body,
            headers=dict(headers),
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        decision = None

    # attach decision to request state so handlers can use it
    request.state.gateway_decision = decision

    response = await call_next(request)
    try:
        if decision is not None:
            response.headers["X-Gateway-Route"] = decision.route
            response.headers["X-Threat-Score"] = str(decision.threat_score)
    except Exception:
        pass
    return response

root_dir = Path(__file__).resolve().parents[2]
frontend_dist = root_dir / "frontend" / "dist"

if frontend_dist.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(frontend_dist / "assets")),
        name="assets",
    )


@app.get("/")
@app.get("/hospital")
@app.get("/admin")
def admin_dashboard() -> FileResponse:
    dashboard_file = frontend_dist / "index.user.html"
    return FileResponse(dashboard_file) if dashboard_file.exists() else FileResponse(root_dir / "frontend" / "index.user.html")


@app.get("/hacker")
def hacker_dashboard() -> FileResponse:
    dashboard_file = frontend_dist / "index.hacker.html"
    return FileResponse(dashboard_file) if dashboard_file.exists() else FileResponse(root_dir / "frontend" / "index.hacker.html")


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/hack.bat")
def download_hack_bat() -> FileResponse:
    return FileResponse(root_dir / "hack.bat", media_type="text/plain", filename="hack.bat")


@app.get("/attack.bat")
def download_attack_bat() -> FileResponse:
    return FileResponse(root_dir / "attack.bat", media_type="text/plain", filename="attack.bat")


@app.get("/tools/security_simulator.py")
def download_security_simulator() -> FileResponse:
    return FileResponse(root_dir / "tools" / "security_simulator.py", media_type="text/plain", filename="security_simulator.py")

