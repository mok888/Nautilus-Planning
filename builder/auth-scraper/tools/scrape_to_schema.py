"""
Scrape selected official docs pages, extract auth-related tokens/headers/endpoint hints,
and generate a canonical JSON Schema for env configuration.

Design:
- Scraping is best-effort and intentionally conservative.
- Canonical keys remain stable; scraping enriches descriptions + patterns where possible.
- You can run this in CI to keep schema fresh.

Usage:
  python tools/scrape_to_schema.py --out config/dex-canonical-env.schema.json
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DocSource:
    name: str
    url: str


DOC_SOURCES: Dict[str, List[DocSource]] = {
    "LIGHTER": [
        DocSource("Lighter API docs (Get Started)", "https://apidocs.lighter.xyz/docs/get-started-for-programmers-1"),
        DocSource("Lighter Python SDK (endpoints list in README)", "https://github.com/elliottech/lighter-python"),
    ],
    "PARADEX": [
        DocSource("Paradex Auth", "https://docs.paradex.trade/docs/trading/api-authentication"),
        DocSource("Paradex Quick Start", "https://docs.paradex.trade/api/general-information/api-quick-start"),
    ],
    "EDGEX": [
        DocSource("EdgeX Auth", "https://edgexhelp.zendesk.com/hc/en-001/articles/14562697621391-Authentication"),
    ],
    "HYPERLIQUID": [
        DocSource("Hyperliquid Info Endpoints (3rd party mirror)", "https://www.quicknode.com/docs/hyperliquid/info-endpoints"),
    ],
    "BACKPACK": [
        DocSource("Backpack API", "https://docs.backpack.exchange/"),
        DocSource("Backpack Support API Docs", "https://support.backpack.exchange/api-docs"),
    ],
    "STANDX": [
        DocSource("StandX API", "https://docs.standx.com/standx-api/standx-api"),
    ],
    "NADO": [
        DocSource("Nado API", "https://docs.nado.xyz/developer-resources/api"),
    ],
    "01XYZ": [
        DocSource("01.xyz API", "https://docs.01.xyz/"),
    ],
    "GRVT": [
        DocSource("GRVT API Docs", "https://api-docs.grvt.io/"),
    ],
}

UA = "dex-auth-automation/0.1 (+https://example.local)"


def fetch_html(url: str, timeout_s: int = 25) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout_s)
    r.raise_for_status()
    return r.text


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def discover_headers(text: str) -> List[str]:
    # captures typical header patterns like X-..., PARADEX-..., etc.
    candidates = set(re.findall(r"\b[A-Z0-9]+(?:-[A-Z0-9]+){1,6}\b", text))
    # filter down to auth-looking headers
    keep = []
    for c in sorted(candidates):
        if any(k in c for k in ["SIGN", "SIGNATURE", "TIMESTAMP", "WINDOW", "API", "AUTH", "ACCOUNT"]):
            keep.append(c)
    return keep[:50]


def discover_paths(text: str) -> List[str]:
    # endpoints like /auth/{public_key}, /info, /status, /api/v1/...
    candidates = set(re.findall(r"(/(?:api/)?v?\d*(?:/[A-Za-z0-9{}_-]+)+)", text))
    # keep relevant short list
    keep = []
    for c in sorted(candidates, key=len):
        if len(c) <= 64:
            keep.append(c)
    return keep[:80]


def scrape_exchange(exchange: str) -> Dict[str, Any]:
    sources = DOC_SOURCES.get(exchange, [])
    merged_text = ""
    for src in sources:
        try:
            merged_text += "\n" + extract_text(fetch_html(src.url))
        except Exception:
            # best-effort
            continue

    return {
        "exchange": exchange,
        "sources": [s.url for s in sources],
        "discovered_headers": discover_headers(merged_text),
        "discovered_paths": discover_paths(merged_text),
    }


def canonical_schema_template(enrichment: Dict[str, Any], *, scrape: bool = True) -> Dict[str, Any]:
    """
    Returns the same canonical schema structure you standardized earlier,
    with optional enrichment attached under x-doc hints.
    """
    x_docs: Dict[str, Any] = {}
    if scrape:
        x_docs = {
            k: scrape_exchange(k)
            for k in [
                "LIGHTER",
                "PARADEX",
                "EDGEX",
                "HYPERLIQUID",
                "BACKPACK",
                "GRVT",
                "NADO",
                "STANDX",
                "01XYZ",
            ]
        }
    # minimal patterns; keep stable
    defs: Dict[str, Any] = {
        "NonEmptyString": {"type": "string", "minLength": 1},
        "Hex0x": {"type": "string", "pattern": "^0x[0-9a-fA-F]+$"},
        "HexNo0x": {"type": "string", "pattern": "^[0-9a-fA-F]+$"},
        "HttpUrl": {"type": "string", "pattern": "^https?://"},
        "WsUrl": {"type": "string", "pattern": "^wss?://"},
        "IntegerString": {"type": "string", "pattern": "^[0-9]+$"},
    }

    schema: Dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.local/schemas/dex-canonical-env.schema.json",
        "title": "Canonical DEX/CEX Auth Env Config",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "LIGHTER": {"$ref": "#/$defs/LighterConfig"},
            "PARADEX": {"$ref": "#/$defs/ParadexConfig"},
            "EDGEX": {"$ref": "#/$defs/EdgexConfig"},
            "HYPERLIQUID": {"$ref": "#/$defs/HyperliquidConfig"},
            "BACKPACK": {"$ref": "#/$defs/BackpackConfig"},
            "STANDX": {"$ref": "#/$defs/StandxConfig"},
            "GRVT": {"$ref": "#/$defs/GrvtConfig"},
            "EXTENDED": {"$ref": "#/$defs/ExtendedConfig"},
            "APEX_OMNI": {"$ref": "#/$defs/ApexOmniConfig"},
            "NADO": {"$ref": "#/$defs/NadoConfig"},
            "01XYZ": {"$ref": "#/$defs/01XYZConfig"},
        },
        "$defs": {
            **defs,
            "LighterConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["LIGHTER_BASE_URL", "LIGHTER_ACCOUNT_INDEX", "LIGHTER_API_KEY_INDEX", "LIGHTER_API_KEY_PRIVATE_KEY"],
                "properties": {
                    "LIGHTER_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "LIGHTER_ACCOUNT_INDEX": {"$ref": "#/$defs/IntegerString"},
                    "LIGHTER_API_KEY_INDEX": {"$ref": "#/$defs/IntegerString"},
                    "LIGHTER_API_KEY_PRIVATE_KEY": {"$ref": "#/$defs/HexNo0x"},
                    "LIGHTER_ETH_PRIVATE_KEY": {"$ref": "#/$defs/Hex0x"},
                    "LIGHTER_WS_URL": {"$ref": "#/$defs/WsUrl"},
                },
                "x-doc": x_docs.get("LIGHTER"),
            },
            "ParadexConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["PARADEX_ENV"],
                "properties": {
                    "PARADEX_ENV": {"type": "string", "enum": ["MAINNET", "TESTNET"]},
                    "PARADEX_MAIN_ACCOUNT_L2_ADDRESS": {"$ref": "#/$defs/Hex0x"},
                    "PARADEX_SUBKEY_PRIVATE_KEY": {"$ref": "#/$defs/Hex0x"},
                    "PARADEX_SUBKEY_PUBLIC_KEY": {"$ref": "#/$defs/Hex0x"},
                    "PARADEX_JWT": {"$ref": "#/$defs/NonEmptyString"},
                },
                "allOf": [
                    {
                        "if": {"required": ["PARADEX_SUBKEY_PRIVATE_KEY"]},
                        "then": {"required": ["PARADEX_MAIN_ACCOUNT_L2_ADDRESS"]},
                    }
                ],
                "x-doc": x_docs.get("PARADEX"),
            },
            "EdgexConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["EDGEX_BASE_URL", "EDGEX_ACCOUNT_ID", "EDGEX_PRIVATE_KEY"],
                "properties": {
                    "EDGEX_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "EDGEX_ACCOUNT_ID": {"$ref": "#/$defs/IntegerString"},
                    "EDGEX_PRIVATE_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "EDGEX_WS_URL": {"$ref": "#/$defs/WsUrl"},
                },
                "x-doc": x_docs.get("EDGEX"),
            },
            "HyperliquidConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["HYPERLIQUID_API_URL", "HYPERLIQUID_ACCOUNT_ADDRESS", "HYPERLIQUID_SECRET_KEY"],
                "properties": {
                    "HYPERLIQUID_API_URL": {"$ref": "#/$defs/HttpUrl"},
                    "HYPERLIQUID_ACCOUNT_ADDRESS": {"$ref": "#/$defs/Hex0x"},
                    "HYPERLIQUID_SECRET_KEY": {"$ref": "#/$defs/Hex0x"},
                },
                "x-doc": x_docs.get("HYPERLIQUID"),
            },
            "BackpackConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["BACKPACK_BASE_URL", "BACKPACK_API_KEY", "BACKPACK_PRIVATE_KEY"],
                "properties": {
                    "BACKPACK_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "BACKPACK_API_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "BACKPACK_PRIVATE_KEY": {"$ref": "#/$defs/NonEmptyString"},
                },
                "x-doc": x_docs.get("BACKPACK"),
            },
            "StandxConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["STANDX_BASE_URL", "STANDX_API_TOKEN", "STANDX_REQUEST_ED25519_PRIVATE_KEY"],
                "properties": {
                    "STANDX_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "STANDX_API_TOKEN": {"type": "string", "minLength": 1, "pattern": "^eyJ"},
                    "STANDX_REQUEST_ED25519_PRIVATE_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "STANDX_WS_MARKET_URL": {"$ref": "#/$defs/WsUrl"},
                    "STANDX_WS_API_URL": {"$ref": "#/$defs/WsUrl"},
                },
                "x-doc": x_docs.get("STANDX"),
            },
            # The following four are kept canonical; you can enrich similarly later.
            "GrvtConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["GRVT_ENV", "GRVT_TRADING_ACCOUNT_ID", "GRVT_API_KEY", "GRVT_PRIVATE_KEY"],
                "properties": {
                    "GRVT_ENV": {"type": "string", "enum": ["testnet", "mainnet"]},
                    "GRVT_TRADING_ACCOUNT_ID": {"$ref": "#/$defs/NonEmptyString"},
                    "GRVT_API_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "GRVT_PRIVATE_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "GRVT_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "GRVT_WS_URL": {"$ref": "#/$defs/WsUrl"},
                },
                "x-doc": x_docs.get("GRVT"),
            },
            "ExtendedConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["EXTENDED_API_KEY", "EXTENDED_STARK_KEY_PUBLIC", "EXTENDED_STARK_KEY_PRIVATE", "EXTENDED_VAULT"],
                "properties": {
                    "EXTENDED_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "EXTENDED_API_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "EXTENDED_STARK_KEY_PUBLIC": {"$ref": "#/$defs/NonEmptyString"},
                    "EXTENDED_STARK_KEY_PRIVATE": {"$ref": "#/$defs/NonEmptyString"},
                    "EXTENDED_VAULT": {"$ref": "#/$defs/NonEmptyString"},
                },
            },
            "ApexOmniConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["APEX_API_KEY", "APEX_API_SECRET", "APEX_API_PASSPHRASE", "APEX_OMNI_KEY_SEED"],
                "properties": {
                    "APEX_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "APEX_API_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "APEX_API_SECRET": {"$ref": "#/$defs/NonEmptyString"},
                    "APEX_API_PASSPHRASE": {"$ref": "#/$defs/NonEmptyString"},
                    "APEX_OMNI_KEY_SEED": {"$ref": "#/$defs/NonEmptyString"},
                },
            },
            "NadoConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["NADO_CHAIN", "NADO_WALLET_PRIVATE_KEY"],
                "properties": {
                    "NADO_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "NADO_CHAIN": {"$ref": "#/$defs/NonEmptyString"},
                    "NADO_WALLET_PRIVATE_KEY": {"$ref": "#/$defs/Hex0x"},
                    "NADO_SUBACCOUNT_OWNER": {"$ref": "#/$defs/Hex0x"},
                    "NADO_SUBACCOUNT_NAME": {"$ref": "#/$defs/NonEmptyString"},
                },
                "x-doc": x_docs.get("NADO"),
            },
            "01XYZConfig": {
                "type": "object",
                "additionalProperties": False,
                "required": ["01XYZ_API_KEY", "01XYZ_API_SECRET"],
                "properties": {
                    "01XYZ_BASE_URL": {"$ref": "#/$defs/HttpUrl"},
                    "01XYZ_WS_URL": {"$ref": "#/$defs/WsUrl"},
                    "01XYZ_API_KEY": {"$ref": "#/$defs/NonEmptyString"},
                    "01XYZ_API_SECRET": {"$ref": "#/$defs/NonEmptyString"},
                    "01XYZ_API_PASSPHRASE": {"$ref": "#/$defs/NonEmptyString"},
                },
                "x-doc": x_docs.get("01XYZ"),
            },
        },
    }
    if enrichment:
        schema["x-enrichment"] = enrichment
    return schema


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output schema path")
    args = ap.parse_args()

    enrichment = {"note": "Schema regenerated from canonical rules; x-doc is best-effort scraping hints."}
    schema = canonical_schema_template(enrichment)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
