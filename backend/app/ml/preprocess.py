import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from pathlib import Path
from typing import Any


def build_simple_feature_set(df: pd.DataFrame) -> pd.DataFrame:
    features = pd.DataFrame()
    features["role"] = df["role"].fillna("unknown").astype(str)
    features["device"] = df["device"].fillna("unknown").astype(str)
    features["browser"] = df["browser"].fillna("unknown").astype(str)
    features["operating_system"] = df["operating_system"].fillna("unknown").astype(str)
    features["country"] = df["country"].fillna("unknown").astype(str)
    features["method"] = df["method"].fillna("GET").astype(str)
    features["path"] = df["path"].fillna("/").astype(str)
    features["body_length"] = df.get("body", pd.Series("", index=df.index)).fillna("").apply(len).astype(float)
    features["param_count"] = df.get("params", pd.Series("", index=df.index)).fillna("").apply(
        lambda value: len(str(value).split("&")) if value else 0
    ).astype(float)
    features["request_frequency"] = df.get("request_frequency", pd.Series(1.0, index=df.index)).fillna(1).astype(float)
    features["login_failures"] = df.get("login_failures", pd.Series(0.0, index=df.index)).fillna(0).astype(float)
    features["ip_address_frequency"] = df.get("ip_address_frequency", pd.Series(1.0, index=df.index)).fillna(1).astype(float)
    features["session_duration"] = df.get("session_duration", pd.Series(60.0, index=df.index)).fillna(60).astype(float)
    features["patient_access_count"] = df.get("patient_access_count", pd.Series(0.0, index=df.index)).fillna(0).astype(float)
    features["time_between_requests"] = df.get("time_between_requests", pd.Series(1.0, index=df.index)).fillna(1).astype(float)
    features["failed_auth_attempts"] = df.get("failed_auth_attempts", pd.Series(0.0, index=df.index)).fillna(0).astype(float)
    return features


def encode_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, LabelEncoder], StandardScaler]:
    encoders: dict[str, LabelEncoder] = {}
    encoded = df.copy()
    for column in ["role", "device", "browser", "operating_system", "country", "method", "path"]:
        encoder = LabelEncoder()
        encoded[column] = encoder.fit_transform(encoded[column].astype(str))
        encoders[column] = encoder

    scaler = StandardScaler()
    numeric_columns = [
        "body_length",
        "param_count",
        "request_frequency",
        "login_failures",
        "ip_address_frequency",
        "session_duration",
        "patient_access_count",
        "time_between_requests",
        "failed_auth_attempts",
    ]
    encoded[numeric_columns] = scaler.fit_transform(encoded[numeric_columns])
    return encoded, encoders, scaler


def transform_features(df: pd.DataFrame, encoders: dict[str, LabelEncoder], scaler: StandardScaler) -> pd.DataFrame:
    transformed = df.copy()
    for column, encoder in encoders.items():
        values = transformed[column].fillna("unknown").astype(str)
        classes = set(encoder.classes_)
        encoded_values = []
        for raw_value in values:
            value = str(raw_value)
            if value in classes:
                encoded_values.append(int(encoder.transform([value])[0]))
            else:
                encoded_values.append(-1)
        transformed[column] = encoded_values

    expected_numeric_features = [
        "body_length",
        "param_count",
        "request_frequency",
        "login_failures",
        "ip_address_frequency",
        "session_duration",
        "patient_access_count",
        "time_between_requests",
        "failed_auth_attempts",
    ]
    if hasattr(scaler, "feature_names_in_"):
        expected_numeric_features = list(scaler.feature_names_in_)

    for feature in expected_numeric_features:
        if feature not in transformed.columns:
            transformed[feature] = 0.0

    numeric_columns = [feature for feature in expected_numeric_features if feature in transformed.columns]
    if numeric_columns:
        transformed[numeric_columns] = scaler.transform(transformed[numeric_columns])
    return transformed
