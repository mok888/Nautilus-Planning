from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import os
import yaml

from builder.infra.yaml_loader import load_research


@dataclass(frozen=True)
class EnvCheckResult:
    missing_by_exchange: Dict[str, List[str]]
    errors: List[str]


def _load_schema(schema_path: Path) -> None:
    """
    Load schema.yaml to ensure it exists and is parseable.
    This keeps env validation aligned with the schema-driven research model.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"schema not found: {schema_path}")
    yaml.safe_load(schema_path.read_text())


def _required_env_for_exchange(exchange_name: str, auth_type: str) -> List[str]:
    exchange_upper = exchange_name.upper()
    
    # Custom overrides for known exchanges with non-standard auth headers
    if exchange_upper == "STANDX":
        return [
            "STANDX_API_TOKEN",
            "STANDX_REQUEST_ED25519_PRIVATE_KEY",
        ]
    if exchange_upper == "EDGEX":
        return [
            "EDGEX_ACCOUNT_ID",
            "EDGEX_STARK_PRIVATE_KEY",
        ]
    if exchange_upper == "GRVT":
        return [
            "GRVT_API_KEY",
            "GRVT_PRIVATE_KEY",
        ]
    if exchange_upper == "LIGHTER":
        return [
            "LIGHTER_API_KEY_PRIVATE_KEY",
            "LIGHTER_API_KEY_INDEX",
            "LIGHTER_ACCOUNT_INDEX",
        ]
    if exchange_upper == "PARADEX":
        return [
            "PARADEX_SUBKEY_PRIVATE_KEY",
            "PARADEX_MAIN_ACCOUNT_L2_ADDRESS",
        ]
    if exchange_upper == "NADO":
        return [
            "NADO_PRIVATE_KEY", 
            "NADO_SUBACCOUNT_ID"
        ]
    if exchange_upper == "APEX_OMNI":
        return [
            "APEX_API_KEY",
            "APEX_API_KEY_SECRET",
            "APEX_API_KEY_PASSPHRASE",
            "APEX_OMNI_KEY_SEED"
        ]
        
    if auth_type in {"HMAC", "JWT", "API_KEY", "SIGNATURE"}:
        return [
            f"{exchange_upper}_API_KEY",
            f"{exchange_upper}_API_SECRET",
        ]
    return []


def validate_env_vars(
    *,
    schema_path: Path = Path("builder/config/schema.yaml"),
    research_root: Path = Path("builder/research"),
    exchange_filter: str | None = None,
) -> EnvCheckResult:
    """
    Validate required env vars for exchanges defined by research YAMLs.
    """
    errors: List[str] = []
    missing_by_exchange: Dict[str, List[str]] = {}

    try:
        _load_schema(schema_path)
    except Exception as exc:
        errors.append(str(exc))
        return EnvCheckResult(missing_by_exchange=missing_by_exchange, errors=errors)

    if not research_root.exists():
        return EnvCheckResult(missing_by_exchange=missing_by_exchange, errors=errors)

    for research_path in sorted(research_root.glob("*.yaml")):
        try:
            spec = load_research(research_path)
        except Exception as exc:
            errors.append(f"{research_path}: {exc}")
            continue

        exchange_name = spec.exchange_identity.exchange_name
        if exchange_filter and exchange_name.lower() != exchange_filter.lower():
            continue
        required = _required_env_for_exchange(exchange_name, spec.authentication.auth_type)
        if not required:
            continue

        missing = [v for v in required if not os.getenv(v)]
        if missing:
            missing_by_exchange[exchange_name] = missing

    return EnvCheckResult(missing_by_exchange=missing_by_exchange, errors=errors)
