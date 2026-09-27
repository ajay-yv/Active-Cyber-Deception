import argparse
import json
import random
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.ml.dataset_loader import load_request_dataset
from app.ml.preprocess import build_simple_feature_set, encode_features

MODEL_DIR = Path(__file__).resolve().parent / "saved_models"
SAMPLE_DATASET_PATH = Path(__file__).resolve().parent / "request_dataset.csv"
MODEL_DIR.mkdir(exist_ok=True)


def generate_sample_request_dataset(num_samples: int = 250) -> pd.DataFrame:
    roles = ["doctor", "nurse", "administrator", "hacker", "anonymous", "researcher"]
    devices = ["trusted", "managed", "personal", "unknown", "lab-equipment"]
    browsers = ["chrome", "firefox", "safari", "curl", "python-requests", "unknown"]
    operating_systems = ["windows", "macos", "linux", "android", "ios", "bot", "unknown"]
    countries = ["us", "gb", "in", "cn", "ru", "high-risk", "unknown"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    paths = [
        "/api/patients",
        "/api/patients/123",
        "/api/auth/login",
        "/api/export",
        "/api/dashboard",
        "/api/security/alerts",
        "/api/patients?patient_id=234",
        "/api/patients?limit=200",
    ]
    bodies = [
        "",
        "{\"update\": \"record\"}",
        "{\"query\": \"status\"}",
        "<script>alert('xss')</script>",
        "SELECT * FROM patients WHERE id = 1;",
        '{"action": "login"}',
    ]
    params = [
        "",
        "page=1",
        "limit=10",
        "patient_id=42",
        "patient_id=42&count=1000",
    ]

    rows: list[dict[str, str | int]] = []
    for i in range(num_samples):
        role = random.choices(roles, weights=[30, 20, 10, 10, 15, 15], k=1)[0]
        path = random.choice(paths)
        body = random.choice(bodies)
        params_string = random.choice(params)
        login_failures = random.choices([0, 1, 2, 3], weights=[70, 20, 7, 3], k=1)[0]
        failed_auth_attempts = random.choices([0, 1, 2, 3, 4], weights=[75, 15, 6, 3, 1], k=1)[0]
        request_frequency = random.uniform(0.1, 10.0)
        ip_address_frequency = random.choice([1, 1, 2, 3, 5, 10])
        session_duration = random.uniform(15.0, 3600.0)
        patient_access_count = random.choice([0, 1, 2, 3, 10])
        time_between_requests = random.uniform(0.1, 300.0)
        label = "normal"
        if role == "hacker" or "SELECT" in body or "script" in body or "/api/export" in path or "limit=200" in path or "count=1000" in params_string or failed_auth_attempts >= 2:
            label = random.choice(["attack", "data_exfiltration", "recon"])

        rows.append(
            {
                "role": role,
                "device": random.choice(devices),
                "browser": random.choice(browsers),
                "operating_system": random.choice(operating_systems),
                "country": random.choice(countries),
                "method": random.choice(methods),
                "path": path,
                "body": body,
                "params": params_string,
                "request_frequency": request_frequency,
                "login_failures": login_failures,
                "ip_address_frequency": ip_address_frequency,
                "session_duration": session_duration,
                "patient_access_count": patient_access_count,
                "time_between_requests": time_between_requests,
                "failed_auth_attempts": failed_auth_attempts,
                "label": label,
            }
        )

    return pd.DataFrame(rows)


def train_models(dataset_path: str | Path | None = None, model_dir: Path | None = None) -> None:
    model_dir = Path(model_dir) if model_dir is not None else MODEL_DIR
    model_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = Path(dataset_path) if dataset_path is not None else SAMPLE_DATASET_PATH
    if not dataset_path.exists():
        df = generate_sample_request_dataset()
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dataset_path, index=False)
        print(f"Generated sample dataset at {dataset_path}")
    else:
        df = load_request_dataset(dataset_path)

    features = build_simple_feature_set(df)
    encoded, encoders, scaler = encode_features(features)

    labels = df["label"].fillna("normal").astype(str)
    label_map = {label: idx for idx, label in enumerate(sorted(labels.unique()))}
    y = labels.map(label_map)

    X_train, X_test, y_train, y_test = train_test_split(encoded, y, test_size=0.2, random_state=42)

    isolation_forest = IsolationForest(n_estimators=128, contamination=0.08, random_state=42)
    isolation_forest.fit(X_train)

    random_forest = RandomForestClassifier(n_estimators=150, class_weight="balanced", random_state=42)
    random_forest.fit(X_train, y_train)

    xgboost = XGBClassifier(n_estimators=150, use_label_encoder=False, eval_metric="logloss", random_state=42)
    xgboost.fit(X_train, y_train)

    joblib.dump(isolation_forest, model_dir / "isolation_forest.joblib")
    joblib.dump(random_forest, model_dir / "random_forest.joblib")
    joblib.dump(xgboost, model_dir / "xgboost.joblib")
    joblib.dump(scaler, model_dir / "scaler.joblib")
    joblib.dump(encoders, model_dir / "encoders.joblib")
    joblib.dump(label_map, model_dir / "label_map.joblib")

    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    y_pred_rf = random_forest.predict(X_test)
    y_pred_xgb = xgboost.predict(X_test)

    metrics = {
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "label_map": label_map,
        "random_forest": {
            "accuracy": float(accuracy_score(y_test, y_pred_rf)),
            "precision": float(precision_score(y_test, y_pred_rf, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, y_pred_rf, average="weighted", zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred_rf, average="weighted", zero_division=0)),
        },
        "xgboost": {
            "accuracy": float(accuracy_score(y_test, y_pred_xgb)),
            "precision": float(precision_score(y_test, y_pred_xgb, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, y_pred_xgb, average="weighted", zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred_xgb, average="weighted", zero_division=0)),
        },
    }
    with open(model_dir / "training_metadata.json", "w", encoding="utf-8") as metadata_file:
        json.dump(metrics, metadata_file, indent=2)

    print(f"Saved models and metadata to {model_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train request security models")
    parser.add_argument("--dataset", default=str(SAMPLE_DATASET_PATH), help="Path to a request dataset CSV file")
    parser.add_argument("--model-dir", default=str(MODEL_DIR), help="Directory where trained models will be saved")
    args = parser.parse_args()
    train_models(args.dataset, args.model_dir)
