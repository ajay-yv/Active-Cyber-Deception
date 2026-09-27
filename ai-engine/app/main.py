from fastapi import FastAPI
from pydantic import BaseModel

from app.twin_generator import TwinGenerator

app = FastAPI(title="AI Twin Engine")
generator = TwinGenerator()


class BatchPatientsPayload(BaseModel):
    patients: list[dict]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/twins/generate")
def generate_twin(patient: dict) -> dict:
    twin = generator.generate(patient)
    return twin.__dict__


@app.post("/twins/evolve")
def evolve_patterns(payload: BatchPatientsPayload) -> dict:
    summary = generator.learn_patterns(payload.patients)
    return {"status": "success", "profile": summary}


@app.get("/twins/profile")
def get_pattern_profile() -> dict:
    return generator.get_profile()

