from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, ensure_directories
from src.feature_engineering import build_features
from src.utils import get_logger, read_csv, write_csv

LOGGER = get_logger(__name__)


def _driver(row: pd.Series) -> str:
    drivers = {
        "loss_ratio": row["loss_ratio"] * 35,
        "claim_frequency": row["claim_frequency"] * 200,
        "manual_override_rate": row["manual_override_rate"] * 4,
        "disengagement_rate": row["disengagement_rate"] * 5,
        "near_miss_rate": row["near_miss_rate"] * 2,
        "sensor_failure_rate": row["sensor_failure_rate"] * 6,
        "environmental_risk": row["environmental_risk_score"] * 0.35,
        "route_complexity": row["route_complexity_score"] * 0.3,
        "maintenance_gap": (100 - row["maintenance_score"]) * 0.45,
        "safety_program_gap": (100 - row["safety_program_score"]) * 0.35,
    }
    return max(drivers, key=drivers.get)


def _recommendation(tier: str, driver: str) -> str:
    if tier == "Critical":
        return "Manual underwriting review"
    if driver in {"maintenance_gap", "sensor_failure_rate"}:
        return "Require maintenance certification"
    if driver in {"loss_ratio", "claim_frequency"}:
        return "Review premium adequacy"
    if driver in {"manual_override_rate", "disengagement_rate", "near_miss_rate"}:
        return "Require safety improvement plan"
    if driver in {"environmental_risk", "route_complexity"}:
        return "Restrict high-risk geography"
    if tier == "High":
        return "Escalate to portfolio manager"
    if tier == "Medium":
        return "Monitor renewal"
    return "Maintain current pricing"


def score_risk(features: pd.DataFrame | None = None) -> pd.DataFrame:
    """Score fleet-month underwriting risk using transparent rules."""
    ensure_directories()
    frame = features.copy() if features is not None else read_csv(DATA_PROCESSED / "fleet_monthly_features.csv")
    if frame.empty:
        frame, _ = build_features()
    score = (
        frame["loss_ratio"].clip(0, 2.5) * 18
        + frame["claim_frequency"].clip(0, 0.25) * 105
        + np.log1p(frame["claim_severity"]).clip(0, 12) * 1.5
        + frame["manual_override_rate"].clip(0, 12) * 2.2
        + frame["disengagement_rate"].clip(0, 12) * 2.4
        + frame["near_miss_rate"].clip(0, 12) * 1.6
        + frame["sensor_failure_rate"].clip(0, 10) * 2.2
        + frame["weather_risk_score"] * 0.08
        + frame["route_complexity_score"] * 0.12
        + (100 - frame["maintenance_score"]) * 0.12
        + (100 - frame["safety_program_score"]) * 0.10
        + frame["autonomy_level"] * 1.2
    ).clip(0, 100)
    frame["risk_score"] = score.round(2)
    frame["risk_tier"] = pd.cut(frame["risk_score"], bins=[-1, 35, 60, 80, 101], labels=["Low", "Medium", "High", "Critical"]).astype(str)
    frame["top_risk_driver"] = frame.apply(_driver, axis=1)
    frame["underwriting_recommendation"] = [_recommendation(tier, driver) for tier, driver in zip(frame["risk_tier"], frame["top_risk_driver"], strict=True)]
    write_csv(frame, DATA_PROCESSED / "fleet_monthly_risk_scores.csv")
    LOGGER.info("risk scoring complete")
    return frame


if __name__ == "__main__":
    score_risk()
