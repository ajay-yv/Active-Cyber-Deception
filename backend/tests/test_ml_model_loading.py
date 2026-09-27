from pathlib import Path

from app.ml.predict import MLModelLoader


def test_ml_model_loader_falls_back_when_artifacts_are_missing(tmp_path: Path) -> None:
    loader = MLModelLoader(model_dir=tmp_path)
    result = loader.predict(
        {
            "role": "doctor",
            "device": "trusted",
            "browser": "chrome",
            "operating_system": "windows",
            "country": "us",
            "method": "GET",
            "path": "/api/patients",
            "body": "",
            "params": "",
        }
    )

    assert result["anomaly_score"] == 0.0
    assert result["anomaly_flag"] == 0
    assert result["random_forest_label"] == "normal"
    assert result["random_forest_confidence"] == 0.0
    assert result["attack_probability"] == 0.0
    assert result["xgboost_confidence"] == 0.0
