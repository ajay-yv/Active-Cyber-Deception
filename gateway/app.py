from dataclasses import dataclass

from fastapi import FastAPI


@dataclass(frozen=True)
class GatewayOutcome:
    route: str
    threat_score: int
    explanation: str


def inspect_request(role: str, device: str, ip_address: str) -> GatewayOutcome:
    if role == "hacker" or device.lower() == "unknown":
        return GatewayOutcome(route="synthetic", threat_score=90, explanation=f"Diverted from {ip_address}")
    return GatewayOutcome(route="real", threat_score=15, explanation="Trusted hospital session")


app = FastAPI(title="AI Security Gateway")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/decision")
def decision(role: str = "hospital_user", device: str = "trusted", ip_address: str = "0.0.0.0") -> dict[str, str | int]:
    outcome = inspect_request(role=role, device=device, ip_address=ip_address)
    return {
        "route": outcome.route,
        "threat_score": outcome.threat_score,
        "explanation": outcome.explanation,
    }
