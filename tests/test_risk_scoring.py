from src.config import VALID_RISK_TIERS
from src.data_generation import generate_all
from src.feature_engineering import build_features
from src.ml_models import train_models
from src.risk_scoring import score_risk


def test_risk_scores_are_between_0_and_100():
    frames = generate_all()
    features, _ = build_features(frames)
    scored = score_risk(features)
    assert scored["risk_score"].between(0, 100).all()


def test_risk_tiers_are_valid():
    frames = generate_all()
    features, _ = build_features(frames)
    scored = score_risk(features)
    assert set(scored["risk_tier"]).issubset(VALID_RISK_TIERS)


def test_ml_training_returns_metrics():
    frames = generate_all()
    features, _ = build_features(frames)
    scored = score_risk(features)
    metrics = train_models(scored)
    assert {"accuracy", "precision", "recall", "f1"}.issubset(metrics["classifier_metrics"])
    assert {"mae", "rmse", "r2"}.issubset(metrics["severity_metrics"])
