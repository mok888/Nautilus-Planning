from __future__ import annotations

import os
import shutil
import subprocess
import typer
import sys
import json
import platform
from typing import Iterable, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from builder.validate_env import validate_env_vars

# Ensure environment variables from .env are loaded
load_dotenv()

REQUIRED_ENV_VARS = [
    # "OPENAI_API_KEY", # No longer strictly required if provider is set
]

OPTIONAL_TOOLS = [
    "git",
    "ruff",
    "pytest",
]


def _check_binary(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    if not path:
        return {
            "ok": False,
            "error": f"{name} not found in PATH",
        }

    try:
        out = subprocess.check_output(
            [name, "--version"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        return {
            "ok": True,
            "version": out,
            "path": path,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"{name} present but failed to execute: {e}",
        }


def _check_env(vars: Iterable[str]) -> list[str]:
    return [v for v in vars if not os.getenv(v)]


def _check_llm_config() -> dict[str, Any]:
    """
    Checks if at least one LLM provider is correctly configured.
    """
    provider = os.getenv("LLM_PROVIDER", "openai")
    
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key:
            return {"ok": True, "provider": "openai", "auth": "env:OPENAI_API_KEY"}
        return {"ok": False, "error": "Missing OPENAI_API_KEY (default provider). Set LLM_PROVIDER=oh-my-opencode to use z.ai."}
    
    if provider == "oh-my-opencode":
        # Check ~/.config/opencode/opencode.json
        config_path = Path.home() / ".config/opencode/opencode.json"
        if not config_path.exists():
             return {"ok": False, "error": f"LLM_PROVIDER=oh-my-opencode set, but {config_path} not found"}
        
        try:
            data = json.loads(config_path.read_text())
            mcp = data.get("mcp", {})
            for server in mcp.values():
                env = server.get("environment", {})
                if "Z_AI_API_KEY" in env:
                    return {"ok": True, "provider": "oh-my-opencode", "auth": f"found Z_AI_API_KEY in {config_path}"}
        except Exception as e:
            return {"ok": False, "error": f"Failed to parse {config_path}: {e}"}
            
        return {"ok": False, "error": f"Z_AI_API_KEY not found in {config_path}"}

    if provider == "glm":
        key = os.getenv("GLM_API_KEY")
        if key:
            return {"ok": True, "provider": "glm", "auth": "env:GLM_API_KEY"}
        return {"ok": False, "error": "Missing GLM_API_KEY for provider=glm"}

    if provider == "opencode-cli":
        # Best-effort check that opencode exists
        res = _check_binary("opencode")
        if res.get("ok"):
            return {"ok": True, "provider": "opencode-cli", "auth": "opencode CLI available"}
        return {"ok": False, "error": "opencode CLI not found in PATH"}

    return {"ok": False, "error": f"Unknown LLM_PROVIDER: {provider}"}


def _fix_instructions() -> dict[str, list[str]]:
    os_name = platform.system().lower()

    if os_name == "darwin":
        return {
            "rust": ["brew install rust"],
            "cargo": ["brew install rust"],
            "git": ["brew install git"],
        }
    elif os_name == "linux":
        return {
            "rust": ["curl https://sh.rustup.rs -sSf | sh"],
            "cargo": ["curl https://sh.rustup.rs -sSf | sh"],
            "git": ["sudo apt install git"],
        }
    elif os_name == "windows":
        return {
            "rust": ["https://rustup.rs"],
            "cargo": ["https://rustup.rs"],
            "git": ["https://git-scm.com/download/win"],
        }
    else:
        return {}


def run_doctor(
    *,
    json_output: bool = False,
    fix: bool = False,
    fail_fast: bool = False,
    exchange: str | None = None,
    allow_env_fail: bool = False,
) -> None:
    report: Dict[str, Any] = {
        "tools": {},
        "env": {},
        "llm": {},
        "ok": True,
    }

    # --- Tools ---
    for tool in ("rustc", "cargo"):
        res = _check_binary(tool)
        report["tools"][tool] = res
        if not res["ok"]:
            report["ok"] = False
            if fail_fast:
                break

    for tool in OPTIONAL_TOOLS:
        report["tools"][tool] = _check_binary(tool)

    # --- LLM Config ---
    llm_res = _check_llm_config()
    report["llm"] = llm_res
    if not llm_res["ok"]:
        report["ok"] = False

    # --- Env vars (Required Generic) ---
    missing_env = _check_env(REQUIRED_ENV_VARS)
    report["env"]["missing"] = missing_env
    if missing_env and not allow_env_fail:
        report["ok"] = False

    # --- Env vars (Schema-derived, per exchange research) ---
    skip_env = os.getenv("DINGER_SKIP_ENV_CHECK", "").strip().lower() in {"1", "true", "yes"}
    env_result = None
    if skip_env:
        report["env"]["skipped"] = True
    else:
        env_result = validate_env_vars(exchange_filter=exchange)
        if env_result.errors:
            report["env"]["schema_errors"] = env_result.errors
            if not allow_env_fail:
                report["ok"] = False
        if env_result.missing_by_exchange:
            report["env"]["missing_by_exchange"] = env_result.missing_by_exchange
            if not allow_env_fail:
                report["ok"] = False

    # --- JSON MODE (CI) ---
    if json_output:
        if fix and not report["ok"]:
            report["fix"] = _fix_instructions()
        print(json.dumps(report, indent=2))
        sys.exit(0 if report["ok"] else 1)

    # --- Human Output ---
    typer.echo("🔍 Builder Doctor\n")

    for name, info in report["tools"].items():
        if info.get("ok"):
            typer.echo(f"✅ {name}: {info.get('version')}")
        else:
            typer.echo(f"❌ {name}: {info.get('error')}")

    if llm_res["ok"]:
        typer.echo(f"✅ LLM ({llm_res['provider']}): {llm_res['auth']}")
    else:
        typer.echo(f"❌ LLM Config: {llm_res['error']}")

    if missing_env:
        prefix = "⚠️" if allow_env_fail else "❌"
        typer.echo(f"{prefix} Missing env vars: {', '.join(missing_env)}")
    if report["env"].get("skipped"):
        typer.echo("⚠️  Env validation skipped (DINGER_SKIP_ENV_CHECK=1).")
    else:
        if env_result and env_result.errors:
            prefix = "⚠️" if allow_env_fail else "❌"
            typer.echo(f"{prefix} Schema/env validation errors:")
            for err in env_result.errors:
                typer.echo(f"   - {err}")
        if env_result and env_result.missing_by_exchange:
            prefix = "⚠️" if allow_env_fail else "❌"
            typer.echo(f"{prefix} Missing exchange env vars:")
            for exchange_name, vars_ in env_result.missing_by_exchange.items():
                typer.echo(f"   - {exchange_name}: {', '.join(vars_)}")

    if fix and not report["ok"]:
        typer.echo("\n🛠 Fix instructions:")
        fixes = _fix_instructions()
        for tool, cmds in fixes.items():
            typer.echo(f"\n{tool}:")
            for c in cmds:
                typer.echo(f"  {c}")

    env_warnings = False
    if missing_env:
        env_warnings = True
    if env_result and (env_result.errors or env_result.missing_by_exchange):
        env_warnings = True

    if not report["ok"]:
        typer.echo("\n❌ Doctor failed.")
        sys.exit(1)

    if allow_env_fail and env_warnings:
        typer.echo("\n✅ Doctor completed with env warnings.")
        return

    typer.echo("\n✅ Doctor passed. Environment is healthy.")
