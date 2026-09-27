from sklearn.ensemble import IsolationForest, RandomForestClassifier
from xgboost import XGBClassifier


def create_models() -> dict[str, object]:
    return {
        "isolation_forest": IsolationForest(n_estimators=128, contamination=0.05, random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "xgboost": XGBClassifier(n_estimators=100, use_label_encoder=False, eval_metric="logloss", random_state=42),
    }
