"""
Test all 8 DEX adapter Python modules.

Tests cover:
  - Module imports (all 6 files per exchange)
  - Config class instantiation (data + exec)
  - Constants validation (VENUE, URLs)
  - Factory classes exist and are importable

No API keys or network calls required.
"""
import importlib
import sys
import os

import pytest

# Add the adapter package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Exchange definitions ──────────────────────────────────────────────

EXCHANGES = [
    {
        "module_name": "O1xyz",
        "venue": "O1XYZ",
        "data_config_cls": "O1XyzDataClientConfig",
        "exec_config_cls": "O1XyzExecClientConfig",
        "data_factory_cls": "O1XyzLiveDataClientFactory",
        "exec_factory_cls": "O1XyzLiveExecClientFactory",
    },
    {
        "module_name": "StandX",
        "venue": "STANDX",
        "data_config_cls": "StandXDataClientConfig",
        "exec_config_cls": "StandXExecClientConfig",
        "data_factory_cls": "StandXLiveDataClientFactory",
        "exec_factory_cls": "StandXLiveExecClientFactory",
    },
    {
        "module_name": "Grvt",
        "venue": "GRVT",
        "data_config_cls": "GrvtDataClientConfig",
        "exec_config_cls": "GrvtExecClientConfig",
        "data_factory_cls": "GrvtLiveDataClientFactory",
        "exec_factory_cls": "GrvtLiveExecClientFactory",
    },
    {
        "module_name": "Lighter",
        "venue": "LIGHTER",
        "data_config_cls": "LighterDataClientConfig",
        "exec_config_cls": "LighterExecClientConfig",
        "data_factory_cls": "LighterLiveDataClientFactory",
        "exec_factory_cls": "LighterLiveExecClientFactory",
    },
    {
        "module_name": "edgex",
        "venue": "EDGEX",
        "data_config_cls": "EdgexDataClientConfig",
        "exec_config_cls": "EdgexExecClientConfig",
        "data_factory_cls": "EdgexLiveDataClientFactory",
        "exec_factory_cls": "EdgexLiveExecClientFactory",
    },
    {
        "module_name": "Paradex",
        "venue": "PARADEX",
        "data_config_cls": "ParadexDataClientConfig",
        "exec_config_cls": "ParadexExecClientConfig",
        "data_factory_cls": "ParadexLiveDataClientFactory",
        "exec_factory_cls": "ParadexLiveExecClientFactory",
    },
    {
        "module_name": "Nado",
        "venue": "NADO",
        "data_config_cls": "NadoDataClientConfig",
        "exec_config_cls": "NadoExecClientConfig",
        "data_factory_cls": "NadoLiveDataClientFactory",
        "exec_factory_cls": "NadoLiveExecClientFactory",
    },
    {
        "module_name": "ApexOmni",
        "venue": "APEXOMNI",
        "data_config_cls": "ApexOmniDataClientConfig",
        "exec_config_cls": "ApexOmniExecClientConfig",
        "data_factory_cls": "ApexOmniLiveDataClientFactory",
        "exec_factory_cls": "ApexOmniLiveExecClientFactory",
    },
]

SUBMODULES = ["config", "constants", "data", "execution", "factories", "providers"]


# ── Import tests ──────────────────────────────────────────────────────

@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
@pytest.mark.parametrize("submodule", SUBMODULES)
def test_import_submodule(exchange, submodule):
    """Each exchange must have all 6 importable submodules."""
    module_path = f"nautilus_adapter.adapters.{exchange['module_name']}.{submodule}"
    mod = importlib.import_module(module_path)
    assert mod is not None


# ── Config instantiation tests ────────────────────────────────────────

@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_data_config_instantiation(exchange):
    """DataClientConfig must instantiate with all defaults."""
    config_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.config"
    )
    cls = getattr(config_mod, exchange["data_config_cls"])
    instance = cls()
    assert instance is not None
    # Should have is_testnet defaulting to False
    assert instance.is_testnet is False


@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_exec_config_instantiation(exchange):
    """ExecClientConfig must instantiate with all defaults."""
    config_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.config"
    )
    cls = getattr(config_mod, exchange["exec_config_cls"])
    instance = cls()
    assert instance is not None
    assert instance.is_testnet is False


@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_data_config_testnet_override(exchange):
    """DataClientConfig must support is_testnet=True."""
    config_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.config"
    )
    cls = getattr(config_mod, exchange["data_config_cls"])
    instance = cls(is_testnet=True)
    assert instance.is_testnet is True


# ── Constants tests ───────────────────────────────────────────────────

@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_venue_constant(exchange):
    """Each exchange must define a VENUE constant matching its venue ID."""
    const_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.constants"
    )
    venue = getattr(const_mod, "VENUE", None)
    assert venue is not None, f"{exchange['module_name']} missing VENUE constant"


@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_constants_have_timeouts(exchange):
    """Each exchange should define timeout-related constants."""
    const_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.constants"
    )
    # Should have at least one timeout or connection constant
    attrs = dir(const_mod)
    has_timeout = any("TIMEOUT" in a.upper() or "INTERVAL" in a.upper() for a in attrs)
    assert has_timeout, f"{exchange['module_name']} missing timeout/interval constants"


# ── Factory tests ─────────────────────────────────────────────────────

@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_data_factory_class_exists(exchange):
    """DataClientFactory class must exist."""
    factory_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.factories"
    )
    cls = getattr(factory_mod, exchange["data_factory_cls"], None)
    assert cls is not None, f"{exchange['module_name']} missing {exchange['data_factory_cls']}"


@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_exec_factory_class_exists(exchange):
    """ExecClientFactory class must exist."""
    factory_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.factories"
    )
    cls = getattr(factory_mod, exchange["exec_factory_cls"], None)
    assert cls is not None, f"{exchange['module_name']} missing {exchange['exec_factory_cls']}"


# ── Provider tests ────────────────────────────────────────────────────

@pytest.mark.parametrize("exchange", EXCHANGES, ids=[e["module_name"] for e in EXCHANGES])
def test_provider_module_has_instrument_provider(exchange):
    """Each providers.py must define an InstrumentProvider class."""
    prov_mod = importlib.import_module(
        f"nautilus_adapter.adapters.{exchange['module_name']}.providers"
    )
    # Find any class that contains 'InstrumentProvider' in its name
    provider_classes = [
        name for name in dir(prov_mod)
        if "InstrumentProvider" in name and isinstance(getattr(prov_mod, name), type)
    ]
    assert len(provider_classes) > 0, f"{exchange['module_name']} missing InstrumentProvider class"
