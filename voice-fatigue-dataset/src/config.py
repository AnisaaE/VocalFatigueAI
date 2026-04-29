from __future__ import annotations

from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config() -> dict:
    """Load the YAML configuration for the dataset pipeline."""
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    return config


def get_data_path(*parts: str) -> Path:
    """Return a target data path relative to the project root."""
    return PROJECT_ROOT.joinpath("data", *parts)
