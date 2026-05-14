from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd


def get_logger(name: str) -> logging.Logger:
    """Return a simple console logger."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    return logging.getLogger(name)


def read_csv(path: Path, parse_dates: list[str] | None = None) -> pd.DataFrame:
    """Read a CSV with consistent encoding."""
    return pd.read_csv(path, parse_dates=parse_dates)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a CSV and ensure its parent exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
