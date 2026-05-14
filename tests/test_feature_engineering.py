from src.data_generation import generate_all
from src.feature_engineering import build_features


def test_engineered_features_contain_required_columns():
    frames = generate_all()
    features, portfolio = build_features(frames)
    required = {
        "claim_frequency",
        "claim_severity",
        "loss_ratio",
        "autonomous_mile_pct",
        "manual_override_rate",
        "disengagement_rate",
        "sensor_failure_rate",
        "software_stability_score",
        "environmental_risk_score",
        "operational_complexity_score",
        "portfolio_risk_score",
        "underwriting_risk_tier",
    }
    assert required.issubset(features.columns)
    assert not portfolio.empty
