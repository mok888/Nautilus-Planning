import yaml
from pathlib import Path
from builder.pipeline.models import ExchangeResearch
from typing import Any

def load_yaml(path: Path) -> Any:
    """
    Load a generic YAML file.
    """
    return yaml.safe_load(path.read_text())

def load_research(path: Path) -> ExchangeResearch:
    data = yaml.safe_load(path.read_text())
    return ExchangeResearch.model_validate(data)
