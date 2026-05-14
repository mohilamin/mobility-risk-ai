from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

from src.config import CHARTS, DATA_PROCESSED, POWERBI_EXPORTS, REPORTS, ensure_directories
from src.data_quality import load_raw
from src.ml_models import train_models
from src.risk_scoring import score_risk
from src.utils import get_logger, read_csv, write_csv

LOGGER = get_logger(__name__)


def export_powerbi() -> dict[str, pd.DataFrame]:
    """Create Power BI-ready CSV exports and business reports."""
    ensure_directories()
    data = load_raw()
    risk = read_csv(DATA_PROCESSED / "fleet_monthly_risk_scores.csv")
    if risk.empty:
        risk = score_risk()
    anomalies = read_csv(DATA_PROCESSED / "anomaly_results.csv") if (DATA_PROCESSED / "anomaly_results.csv").exists() else pd.DataFrame()
    importance = read_csv(DATA_PROCESSED / "ml_feature_importance.csv") if (DATA_PROCESSED / "ml_feature_importance.csv").exists() else pd.DataFrame()
    claims = data["claims"]
    exposure = data["exposure"]
    interactions = data["client_interactions"]
    latest = risk.sort_values("month").groupby("fleet_id").tail(1)
    portfolio_dashboard = (
        risk.groupby(["month", "client_type", "primary_state", "risk_tier"], as_index=False)
        .agg(earned_premium=("earned_premium", "sum"), incurred_loss=("incurred_loss", "sum"), avg_risk_score=("risk_score", "mean"), fleets=("fleet_id", "nunique"))
    )
    portfolio_dashboard["loss_ratio"] = portfolio_dashboard["incurred_loss"] / portfolio_dashboard["earned_premium"].clip(lower=1)
    underwriting = latest[
        [
            "fleet_id",
            "client_name",
            "client_type",
            "primary_state",
            "autonomy_level",
            "risk_score",
            "risk_tier",
            "top_risk_driver",
            "underwriting_recommendation",
            "loss_ratio",
            "claim_frequency",
            "manual_override_rate",
        ]
    ]
    claims_dashboard = claims.merge(data["fleets"][["fleet_id", "client_type", "primary_state"]], on="fleet_id", how="left")
    exposure_dashboard = exposure.merge(data["fleets"][["fleet_id", "client_type", "primary_state", "autonomy_level"]], on="fleet_id", how="left")
    ml_risk_scores = latest[["fleet_id", "client_name", "risk_score", "risk_tier", "top_risk_driver", "underwriting_recommendation"]]
    anomaly_alerts = anomalies.loc[anomalies["anomaly_flag"] == True] if not anomalies.empty else pd.DataFrame()
    interaction_summary = interactions.groupby(["fleet_id", "interaction_type", "business_owner"], as_index=False).agg(interactions=("interaction_id", "count"), follow_ups=("follow_up_required", "sum"))
    exports = {
        "portfolio_dashboard": portfolio_dashboard,
        "underwriting_account_summary": underwriting,
        "claims_dashboard": claims_dashboard,
        "exposure_dashboard": exposure_dashboard,
        "ml_risk_scores": ml_risk_scores,
        "anomaly_alerts": anomaly_alerts,
        "client_interaction_summary": interaction_summary,
    }
    for name, frame in exports.items():
        write_csv(frame, POWERBI_EXPORTS / f"{name}.csv")
    _write_charts(risk, underwriting)
    _write_reports(risk, underwriting, importance)
    LOGGER.info("Power BI exports and reports written")
    return exports


def _write_charts(risk: pd.DataFrame, underwriting: pd.DataFrame) -> None:
    """Write lightweight static charts for GitHub review."""
    risk_by_tier = underwriting["risk_tier"].value_counts().reindex(["Low", "Medium", "High", "Critical"]).fillna(0)
    fig, ax = plt.subplots(figsize=(7, 4))
    risk_by_tier.plot(kind="bar", ax=ax, color=["#2ca25f", "#fed976", "#fd8d3c", "#de2d26"])
    ax.set_title("Latest Fleet Risk Tier Distribution")
    ax.set_xlabel("Risk tier")
    ax.set_ylabel("Fleets")
    fig.tight_layout()
    fig.savefig(CHARTS / "risk_tier_distribution.png", dpi=150)
    plt.close(fig)

    trend = risk.groupby("month", as_index=False)["risk_score"].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(pd.to_datetime(trend["month"]), trend["risk_score"], color="#3182bd")
    ax.set_title("Average Portfolio Risk Score Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Risk score")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(CHARTS / "portfolio_risk_trend.png", dpi=150)
    plt.close(fig)


def _write_reports(risk: pd.DataFrame, underwriting: pd.DataFrame, importance: pd.DataFrame) -> None:
    total_premium = risk.groupby("fleet_id")["earned_premium"].first().sum()
    total_loss = risk["incurred_loss"].sum()
    high_accounts = underwriting["risk_tier"].isin(["High", "Critical"]).sum()
    (REPORTS / "executive_summary.md").write_text(
        "\n".join(
            [
                "# Executive Summary",
                "",
                "This synthetic prototype evaluates autonomous and rideshare mobility portfolio risk for commercial insurance teams.",
                f"- Estimated earned premium: ${total_premium:,.0f}",
                f"- Incurred loss in synthetic claims: ${total_loss:,.0f}",
                f"- High or critical accounts in latest month: {high_accounts}",
                "",
                "The platform combines exposure, claims, vehicle autonomy, sensor, software, maintenance, and environmental risk indicators.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORTS / "underwriting_recommendations.md").write_text(
        "\n".join(
            [
                "# Underwriting Recommendations",
                "",
                "Underwriters can use the risk score to triage accounts for pricing review, renewal action, deductible changes, safety improvement plans, and manual referral.",
                "",
                "High-risk signals include elevated loss ratio, claim frequency, manual overrides, disengagements, sensor failures, route complexity, poor maintenance, and weak safety programs.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORTS / "powerbi_dashboard_spec.md").write_text(
        "\n".join(
            [
                "# Power BI Dashboard Specification",
                "",
                "## Dashboard 1: Executive Portfolio Overview",
                "Total premium, total incurred loss, portfolio loss ratio, high-risk accounts, risk by client type, loss ratio by state, trend over time.",
                "",
                "## Dashboard 2: Underwriting Intelligence",
                "Risk score by fleet, top risk drivers, pricing review queue, renewal review queue, underwriting recommendations.",
                "",
                "## Dashboard 3: Autonomous Mobility Risk",
                "Autonomy level risk comparison, manual overrides, disengagements, near-miss trends, sensor failure trends, software version risk.",
                "",
                "## Dashboard 4: Claims & Exposure",
                "Claims frequency, claim severity, litigation rate, bodily injury exposure, weather-related losses, severity hotspots.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    top = importance.head(8)["feature"].tolist() if not importance.empty else []
    (REPORTS / "data_dictionary.md").write_text(
        "\n".join(
            [
                "# Data Dictionary",
                "",
                "## fleets.csv",
                "Account-level commercial mobility client profile including fleet size, client type, region, state, autonomy level, mileage, safety, maintenance, growth, and account owner.",
                "",
                "## vehicles.csv",
                "Vehicle-level fleet assets including autonomy capability, sensor vendor, software version, sensor flags, utilization, and maintenance.",
                "",
                "## exposure.csv",
                "Monthly vehicle exposure including miles, autonomous/manual split, overrides, disengagements, near misses, emergency braking, weather, congestion, route complexity, sensor failures, software updates, and AI confidence.",
                "",
                "## policies.csv",
                "Policy terms, premium, limit, deductible, underwriting tier, pricing score, renewal status, and active status.",
                "",
                "## claims.csv",
                "Claim-level losses, reserves, litigation, injury/property flags, software/sensor indicators, weather, severity, recovery, and close time.",
                "",
                "## client_interactions.csv",
                "Portfolio and account management touchpoints with recommendations, follow-ups, topics, and owners.",
                "",
                f"## Top ML Features Observed: {', '.join(top)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_reporting() -> dict[str, pd.DataFrame]:
    """Ensure models exist and export report assets."""
    if not (DATA_PROCESSED / "ml_feature_importance.csv").exists():
        train_models()
    return export_powerbi()


if __name__ == "__main__":
    run_reporting()
