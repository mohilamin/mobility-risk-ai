from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score
from sklearn.model_selection import train_test_split

from src.config import DATA_PROCESSED, MODEL_ARTIFACTS, REPORTS, RANDOM_SEED, ensure_directories
from src.risk_scoring import score_risk
from src.utils import get_logger, read_csv, write_csv

LOGGER = get_logger(__name__)

FEATURE_COLUMNS = [
    "loss_ratio",
    "claim_frequency",
    "claim_severity",
    "autonomous_mile_pct",
    "manual_override_rate",
    "disengagement_rate",
    "near_miss_rate",
    "emergency_braking_rate",
    "sensor_failure_rate",
    "software_stability_score",
    "environmental_risk_score",
    "operational_complexity_score",
    "maintenance_score",
    "safety_program_score",
    "autonomy_level",
]
SEVERITY_FEATURE_COLUMNS = [feature for feature in FEATURE_COLUMNS if feature != "claim_severity"]


def train_models(scored: pd.DataFrame | None = None) -> dict[str, object]:
    """Train classifier, severity regressor, and anomaly detector."""
    ensure_directories()
    data = scored.copy() if scored is not None else read_csv(DATA_PROCESSED / "fleet_monthly_risk_scores.csv")
    if data.empty:
        data = score_risk()
    model_data = data[FEATURE_COLUMNS + ["risk_tier"]].replace([np.inf, -np.inf], 0).fillna(0)
    x = model_data[FEATURE_COLUMNS]
    y = model_data["risk_tier"].isin(["High", "Critical"]).astype(int)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y)
    clf = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=RANDOM_SEED, class_weight="balanced")
    clf.fit(x_train, y_train)
    pred = clf.predict(x_test)
    classifier_metrics = {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
    }
    reg_y = data["claim_severity"].replace([np.inf, -np.inf], 0).fillna(0)
    x_severity = model_data[SEVERITY_FEATURE_COLUMNS]
    xr_train, xr_test, yr_train, yr_test = train_test_split(x_severity, reg_y, test_size=0.25, random_state=RANDOM_SEED)
    reg = RandomForestRegressor(n_estimators=80, max_depth=10, random_state=RANDOM_SEED)
    reg.fit(xr_train, yr_train)
    reg_pred = reg.predict(xr_test)
    severity_metrics = {
        "mae": round(float(mean_absolute_error(yr_test, reg_pred)), 2),
        "rmse": round(float(mean_squared_error(yr_test, reg_pred) ** 0.5), 2),
        "r2": round(float(r2_score(yr_test, reg_pred)), 4),
    }
    iso = IsolationForest(n_estimators=80, contamination=0.06, random_state=RANDOM_SEED)
    anomaly_score = iso.fit_predict(x)
    data["anomaly_score"] = iso.decision_function(x).round(4)
    data["anomaly_flag"] = anomaly_score == -1
    severity_importance = pd.Series(reg.feature_importances_, index=SEVERITY_FEATURE_COLUMNS).reindex(FEATURE_COLUMNS, fill_value=0)
    importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "classifier_importance": clf.feature_importances_,
            "severity_importance": severity_importance.to_numpy(),
        }
    ).sort_values("classifier_importance", ascending=False)
    (MODEL_ARTIFACTS / "risk_classifier.pkl").write_bytes(pickle.dumps(clf))
    (MODEL_ARTIFACTS / "severity_model.pkl").write_bytes(pickle.dumps(reg))
    write_csv(importance, DATA_PROCESSED / "ml_feature_importance.csv")
    write_csv(data[["fleet_id", "month", "risk_score", "risk_tier", "anomaly_score", "anomaly_flag", "top_risk_driver"]], DATA_PROCESSED / "anomaly_results.csv")
    summary = {"risk_classifier": classifier_metrics, "severity_regressor": severity_metrics}
    (MODEL_ARTIFACTS / "model_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# Model Summary",
        "",
        "ML supports human underwriting judgment; it does not replace it.",
        "",
        "## Risk Tier Classifier",
        f"- Accuracy: {classifier_metrics['accuracy']}",
        f"- Precision: {classifier_metrics['precision']}",
        f"- Recall: {classifier_metrics['recall']}",
        f"- F1: {classifier_metrics['f1']}",
        "",
        "## Claim Severity Regressor",
        f"- MAE: {severity_metrics['mae']}",
        f"- RMSE: {severity_metrics['rmse']}",
        f"- R2: {severity_metrics['r2']}",
        "",
        "## Governance",
        "Outputs are AI-assisted underwriting intelligence for review, pricing, and portfolio triage.",
    ]
    (REPORTS / "model_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    LOGGER.info("ML models trained")
    return {"classifier_metrics": classifier_metrics, "severity_metrics": severity_metrics}


if __name__ == "__main__":
    train_models()
