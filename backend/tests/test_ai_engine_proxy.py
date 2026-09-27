import time

import app.services.ai_engine_proxy as ai_engine_proxy


class SlowClient:
    def __init__(self, timeout):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        if self.timeout >= 1:
            time.sleep(0.2)
        else:
            time.sleep(0.01)
        raise RuntimeError("simulated remote failure")


def test_generate_falls_back_quickly_when_remote_engine_is_unavailable(monkeypatch):
    monkeypatch.setattr(ai_engine_proxy.httpx, "Client", SlowClient)

    start = time.perf_counter()
    twin = ai_engine_proxy.TwinGeneratorProxy().generate(
        {
            "id": "patient-1",
            "name": "Alice",
            "age": 40,
            "disease": "Fever",
            "diagnosis": "Flu",
            "medicines": [],
            "treatment_pattern": "Standard",
        }
    )
    elapsed = time.perf_counter() - start

    assert twin["synthetic_patient_id"].lower().startswith("syn-")
    assert elapsed < 0.15
