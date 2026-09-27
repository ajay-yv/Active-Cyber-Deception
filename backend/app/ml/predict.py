import logging
from pathlib import Path

import joblib
import pandas as pd
from app.ml.preprocess import build_simple_feature_set, transform_features

MODEL_DIR = Path(__file__).resolve().parent / "saved_models"
_logger = logging.getLogger(__name__)


class MLModelLoader:
    def __init__(self, model_dir: Path | None = None) -> None:
        self.model_dir = Path(model_dir) if model_dir is not None else MODEL_DIR
        self.isolation_forest = None
        self.random_forest = None
        self.xgboost = None
        self.scaler = None
        self.encoders = None
        self.label_map: dict[str, int] = {}
        self.inverse_label_map: dict[int, str] = {}
        self.loaded = False
        self.load_models()

    def load_models(self) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.isolation_forest = joblib.load(self.model_dir / "isolation_forest.joblib")
            self.random_forest = joblib.load(self.model_dir / "random_forest.joblib")
            self.xgboost = joblib.load(self.model_dir / "xgboost.joblib")
            self.scaler = joblib.load(self.model_dir / "scaler.joblib")
            self.encoders = joblib.load(self.model_dir / "encoders.joblib")
            self.label_map = joblib.load(self.model_dir / "label_map.joblib")
            self.inverse_label_map = {v: k for k, v in self.label_map.items()}
            self.loaded = True
        except FileNotFoundError as exc:
            _logger.warning("Missing AI model artifact while loading models from %s: %s", self.model_dir, exc)
            self.loaded = False
        except Exception as exc:
            _logger.warning("Failed to initialize AI model loader from %s: %s", self.model_dir, exc)
            self.loaded = False

    def _default_predictions(self) -> dict[str, object]:
        return {
            "anomaly_score": 0.0,
            "anomaly_flag": 0,
            "random_forest_label": "normal",
            "random_forest_confidence": 0.0,
            "attack_probability": 0.0,
            "xgboost_confidence": 0.0,
        }

    def predict(self, request_context: dict[str, str | int]) -> dict[str, object]:
        if not self.loaded:
            return self._default_predictions()

        try:
            df = pd.DataFrame([request_context])
            features = build_simple_feature_set(df)
            transformed = transform_features(features, self.encoders, self.scaler)

            # Ensure the feature shape matches the model training dataset in case the training schema changed.
            expected_columns = None
            if hasattr(self.random_forest, "feature_names_in_"):
                expected_columns = list(self.random_forest.feature_names_in_)
            elif hasattr(self.xgboost, "feature_names_in_"):
                expected_columns = list(self.xgboost.feature_names_in_)
            if expected_columns is not None:
                for feature in expected_columns:
                    if feature not in transformed.columns:
                        transformed[feature] = 0.0
                transformed = transformed.reindex(columns=expected_columns, fill_value=0.0)

            anomaly_score = float(self.isolation_forest.decision_function(transformed)[0])
            anomaly_flag = int(anomaly_score < -0.15)

            rf_probs = self.random_forest.predict_proba(transformed)[0]
            rf_label_index = int(self.random_forest.predict(transformed)[0])
            rf_label = self.inverse_label_map.get(rf_label_index, "normal")
            rf_confidence = float(max(rf_probs)) if len(rf_probs) else 0.0

            xgb_probs = self.xgboost.predict_proba(transformed)[0]
            normal_label_idx = self.label_map.get("normal")
            if normal_label_idx is not None and 0 <= normal_label_idx < len(xgb_probs):
                attack_prob = float((1.0 - xgb_probs[normal_label_idx]) * 100.0)
            else:
                attack_prob = float(max(xgb_probs)) * 100.0
            xgb_confidence = float(max(xgb_probs)) if len(xgb_probs) else 0.0

            return {
                "anomaly_score": anomaly_score,
                "anomaly_flag": anomaly_flag,
                "random_forest_label": rf_label,
                "random_forest_confidence": round(rf_confidence, 4),
                "attack_probability": round(attack_prob, 2),
                "xgboost_confidence": round(xgb_confidence, 4),
            }
        except Exception as exc:
            _logger.warning("AI prediction failed, falling back to defaults: %s", exc)
            return self._default_predictions()
