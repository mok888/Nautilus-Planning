"""
Load env (.env or env.json), normalize to schema structure, validate with Draft2020-12.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import dotenv_values
from jsonschema import Draft202012Validator

EXCHANGE_PREFIXES = [
    "LIGHTER",
    "PARADEX",
    "EDGEX",
    "HYPERLIQUID",
    "BACKPACK",
    "STANDX",
    "GRVT",
    "EXTENDED",
    "APEX_OMNI",
    "NADO",
    "01XYZ",
]


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


def load_schema(schema_path: str | Path) -> Dict[str, Any]:
    p = Path(schema_path)
    return json.loads(p.read_text(encoding="utf-8"))


def load_env_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def load_dotenv(path: str | Path) -> Dict[str, str]:
    # python-dotenv handles quotes/comments robustly
    vals = dotenv_values(str(path))
    return {k: v for k, v in vals.items() if k and v is not None}


def dotenv_to_structured(env: Dict[str, str]) -> Dict[str, Any]:
    structured: Dict[str, Any] = {}
    for prefix in EXCHANGE_PREFIXES:
        block = {k: v for k, v in env.items() if k.startswith(prefix + "_")}
        if block:
            structured[prefix] = block
    return structured


def validate(schema: Dict[str, Any], instance: Dict[str, Any]) -> List[ValidationIssue]:
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema)
    issues: List[ValidationIssue] = []
    for err in sorted(v.iter_errors(instance), key=lambda e: list(e.path)):
        path = "$" + "".join(f"[{json.dumps(p)}]" for p in err.path)
        issues.append(ValidationIssue(path=path, message=err.message))
    return issues


def load_and_validate(
    schema_path: str | Path,
    *,
    env_json_path: Optional[str | Path] = None,
    dotenv_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    if bool(env_json_path) == bool(dotenv_path):
        raise ValueError("Provide exactly one of env_json_path or dotenv_path")

    schema = load_schema(schema_path)

    if env_json_path:
        instance = load_env_json(env_json_path)
    else:
        env = load_dotenv(dotenv_path)  # type: ignore[arg-type]
        instance = dotenv_to_structured(env)

    issues = validate(schema, instance)
    if issues:
        msg = "\n".join([f"- {i.path}: {i.message}" for i in issues])
        raise ValueError(f"Config validation failed:\n{msg}")

    return instance
