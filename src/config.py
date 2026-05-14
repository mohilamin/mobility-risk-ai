from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
POWERBI_EXPORTS = PROJECT_ROOT / "data" / "powerbi_exports"
REPORTS = PROJECT_ROOT / "reports"
CHARTS = PROJECT_ROOT / "outputs" / "charts"
MODEL_ARTIFACTS = PROJECT_ROOT / "outputs" / "model_artifacts"
RANDOM_SEED = 42

VALID_RISK_TIERS = {"Low", "Medium", "High", "Critical"}


def ensure_directories() -> None:
    """Create project output directories."""
    for path in [DATA_RAW, DATA_PROCESSED, POWERBI_EXPORTS, REPORTS, CHARTS, MODEL_ARTIFACTS]:
        path.mkdir(parents=True, exist_ok=True)
