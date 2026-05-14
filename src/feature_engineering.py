from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, ensure_directories
from src.data_quality import load_raw
from src.utils import get_logger, write_csv

LOGGER = get_logger(__name__)


def build_features(frames: dict[str, pd.DataFrame] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build fleet monthly risk features and portfolio summary."""
    ensure_directories()
    data = frames or load_raw()
    fleets = data["fleets"]
    exposure = data["exposure"].copy()
    policies = data["policies"]
    claims = data["claims"].copy()
    exposure["month"] = pd.to_datetime(exposure["month"]).dt.to_period("M").dt.to_timestamp()
    claims["month"] = pd.to_datetime(claims["loss_date"]).dt.to_period("M").dt.to_timestamp()

    exposure_month = (
        exposure.groupby(["fleet_id", "month"], as_index=False)
        .agg(
            miles_driven=("miles_driven", "sum"),
            autonomous_miles=("autonomous_miles", "sum"),
            manual_miles=("manual_miles", "sum"),
            autonomous_hours=("autonomous_hours", "sum"),
            manual_override_count=("manual_override_count", "sum"),
            disengagement_count=("disengagement_count", "sum"),
            near_miss_events=("near_miss_events", "sum"),
            emergency_braking_events=("emergency_braking_events", "sum"),
            sensor_failure_events=("sensor_failure_events", "sum"),
            weather_risk_score=("weather_risk_score", "mean"),
            congestion_score=("congestion_score", "mean"),
            route_complexity_score=("route_complexity_score", "mean"),
            pedestrian_density_score=("pedestrian_density_score", "mean"),
            construction_zone_exposure=("construction_zone_exposure", "mean"),
            ai_confidence_avg=("ai_confidence_avg", "mean"),
        )
    )
    claims_month = claims.groupby(["fleet_id", "month"], as_index=False).agg(claim_count=("claim_id", "count"), incurred_loss=("incurred_loss", "sum"))
    policy = policies.groupby("fleet_id", as_index=False).agg(earned_premium=("earned_premium", "sum"), written_premium=("written_premium", "sum"))
    features = exposure_month.merge(claims_month, how="left", on=["fleet_id", "month"]).merge(policy, how="left", on="fleet_id").merge(fleets, how="left", on="fleet_id")
    features[["claim_count", "incurred_loss"]] = features[["claim_count", "incurred_loss"]].fillna(0)
    exposure_units = features["miles_driven"].clip(lower=1) / 1000
    features["claim_frequency"] = features["claim_count"] / exposure_units
    features["claim_severity"] = features["incurred_loss"] / features["claim_count"].replace(0, np.nan)
    features["claim_severity"] = features["claim_severity"].fillna(0)
    features["loss_ratio"] = features["incurred_loss"] / (features["earned_premium"].clip(lower=1) / 12)
    features["autonomous_mile_pct"] = features["autonomous_miles"] / features["miles_driven"].clip(lower=1)
    features["manual_override_rate"] = features["manual_override_count"] / features["autonomous_miles"].clip(lower=1) * 1000
    features["disengagement_rate"] = features["disengagement_count"] / features["autonomous_miles"].clip(lower=1) * 1000
    features["near_miss_rate"] = features["near_miss_events"] / exposure_units
    features["emergency_braking_rate"] = features["emergency_braking_events"] / exposure_units
    features["sensor_failure_rate"] = features["sensor_failure_events"] / features["autonomous_miles"].clip(lower=1) * 1000
    features["software_stability_score"] = (100 - features["sensor_failure_rate"] * 6 - features["disengagement_rate"] * 3).clip(0, 100)
    features["environmental_risk_score"] = (features["weather_risk_score"] * 0.35 + features["congestion_score"] * 0.25 + features["pedestrian_density_score"] * 0.25 + features["construction_zone_exposure"] * 100 * 0.15)
    features["operational_complexity_score"] = (features["route_complexity_score"] * 0.45 + features["manual_override_rate"] * 2.5 + features["near_miss_rate"] * 1.2).clip(0, 100)
    features["portfolio_risk_score"] = (
        features["loss_ratio"].clip(0, 2.5) * 22
        + features["claim_frequency"].clip(0, 0.25) * 120
        + features["environmental_risk_score"] * 0.2
        + features["operational_complexity_score"] * 0.25
        + (100 - features["maintenance_score"]) * 0.15
        + (100 - features["safety_program_score"]) * 0.12
    ).clip(0, 100)
    features["underwriting_risk_tier"] = pd.cut(features["portfolio_risk_score"], bins=[-1, 35, 60, 80, 101], labels=["Low", "Medium", "High", "Critical"]).astype(str)
    portfolio = (
        features.groupby(["client_type", "primary_state"], as_index=False)
        .agg(
            fleets=("fleet_id", "nunique"),
            total_miles=("miles_driven", "sum"),
            total_incurred_loss=("incurred_loss", "sum"),
            earned_premium=("earned_premium", "sum"),
            avg_risk_score=("portfolio_risk_score", "mean"),
            high_risk_months=("underwriting_risk_tier", lambda s: int(s.isin(["High", "Critical"]).sum())),
        )
    )
    portfolio["loss_ratio"] = portfolio["total_incurred_loss"] / portfolio["earned_premium"].clip(lower=1)
    write_csv(features, DATA_PROCESSED / "fleet_monthly_features.csv")
    write_csv(portfolio, DATA_PROCESSED / "portfolio_summary.csv")
    LOGGER.info("feature engineering complete")
    return features, portfolio


if __name__ == "__main__":
    build_features()
