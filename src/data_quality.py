from __future__ import annotations

import pandas as pd

from src.config import DATA_PROCESSED, DATA_RAW, REPORTS, ensure_directories
from src.utils import get_logger, read_csv, write_csv

LOGGER = get_logger(__name__)


def load_raw() -> dict[str, pd.DataFrame]:
    """Load raw synthetic datasets."""
    return {
        "fleets": read_csv(DATA_RAW / "fleets.csv"),
        "vehicles": read_csv(DATA_RAW / "vehicles.csv", parse_dates=["last_maintenance_date"]),
        "exposure": read_csv(DATA_RAW / "exposure.csv", parse_dates=["month"]),
        "policies": read_csv(DATA_RAW / "policies.csv", parse_dates=["effective_date", "expiration_date"]),
        "claims": read_csv(DATA_RAW / "claims.csv", parse_dates=["loss_date", "report_date"]),
        "client_interactions": read_csv(DATA_RAW / "client_interactions.csv", parse_dates=["interaction_date"]),
    }


def _issue(check_name: str, severity: str, count: int, description: str) -> dict[str, object]:
    return {"check_name": check_name, "severity": severity, "issue_count": int(count), "description": description}


def run_quality_checks(frames: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Run data quality checks and write issue reports."""
    ensure_directories()
    data = frames or load_raw()
    fleets = data["fleets"]
    vehicles = data["vehicles"]
    exposure = data["exposure"]
    policies = data["policies"]
    claims = data["claims"]
    issues = [
        _issue("duplicate_policy_ids", "high", policies["policy_id"].duplicated().sum(), "Policy IDs should be unique."),
        _issue("missing_fleet_ids", "critical", sum(frame["fleet_id"].isna().sum() for frame in [fleets, vehicles, exposure, policies, claims]), "Fleet IDs are required across core tables."),
        _issue("claims_without_policies", "critical", (~claims["policy_id"].isin(policies["policy_id"])).sum(), "Every claim must map to a policy."),
        _issue("vehicles_without_fleets", "critical", (~vehicles["fleet_id"].isin(fleets["fleet_id"])).sum(), "Every vehicle must map to a fleet."),
        _issue("exposure_without_vehicles", "critical", (~exposure["vehicle_id"].isin(vehicles["vehicle_id"])).sum(), "Every exposure record must map to a vehicle."),
        _issue("negative_premium", "critical", (policies["written_premium"] < 0).sum(), "Premium cannot be negative."),
        _issue("negative_incurred_loss", "critical", (claims["incurred_loss"] < 0).sum(), "Incurred loss cannot be negative."),
        _issue("invalid_autonomy_levels", "high", (~fleets["autonomy_level"].between(0, 5)).sum() + (~vehicles["autonomy_level"].between(0, 5)).sum(), "Autonomy level must be 0 through 5."),
        _issue("expired_policies_marked_active", "medium", ((policies["expiration_date"] < pd.Timestamp("2025-12-31")) & policies["active_flag"]).sum(), "Expired policies should not be active."),
        _issue("claims_reported_before_loss", "critical", (claims["report_date"] < claims["loss_date"]).sum(), "Claims cannot be reported before loss date."),
        _issue("earned_premium_gt_written", "high", (policies["earned_premium"] > policies["written_premium"]).sum(), "Earned premium should not exceed written premium."),
        _issue("missing_sensor_data_autonomy_4_5", "high", (((vehicles["autonomy_level"] >= 4) & ~(vehicles["lidar_enabled"] & vehicles["camera_enabled"] & vehicles["radar_enabled"]))).sum(), "Level 4/5 vehicles should have lidar, camera, and radar enabled."),
        _issue("unusually_high_manual_override_rates", "medium", ((exposure["manual_override_count"] / exposure["autonomous_miles"].clip(lower=1) * 1000) > 15).sum(), "Manual override rate should be reviewed when above 15 per 1,000 autonomous miles."),
        _issue("unmatched_policy_claim_exposure_records", "critical", (~claims["vehicle_id"].isin(exposure["vehicle_id"])).sum(), "Claimed vehicles should have exposure records."),
    ]
    report = pd.DataFrame(issues)
    write_csv(report, DATA_PROCESSED / "data_quality_issues.csv")
    failing = report.loc[report["issue_count"] > 0]
    lines = ["# Data Quality Report", "", f"Total checks: {len(report)}", f"Checks with findings: {len(failing)}", ""]
    for _, row in report.iterrows():
        lines.append(f"- **{row['check_name']}** ({row['severity']}): {row['issue_count']} findings. {row['description']}")
    (REPORTS / "data_quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    LOGGER.info("data quality checks complete")
    return report


if __name__ == "__main__":
    run_quality_checks()
