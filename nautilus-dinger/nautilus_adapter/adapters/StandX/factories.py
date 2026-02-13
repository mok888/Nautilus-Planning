import asyncio
import importlib
import importlib.util
import os
from pathlib import Path
from typing import Any

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.config import LiveDataClientConfig, LiveExecClientConfig
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.model.identifiers import ClientId

from .config import StandXDataClientConfig, StandXExecClientConfig
from .constants import REST_URL_MAINNET, REST_URL_TESTNET, VENUE
from .data import StandXDataClient
from .execution import StandXExecutionClient
from .providers import StandXInstrumentProvider


def _import_standx_backend() -> object | None:
    try:
        return importlib.import_module("standx")
    except Exception:
        pass

    adapters_root = Path(__file__).resolve().parents[3]
    workspace_root = adapters_root.parent
    candidates = [
        workspace_root / "target" / "debug" / "standx.so",
        workspace_root / "target" / "debug" / "deps" / "standx.so",
        workspace_root / "target" / "debug" / "deps" / "libstandx.so",
        workspace_root / "target" / "release" / "standx.so",
        workspace_root / "target" / "release" / "deps" / "standx.so",
        workspace_root / "target" / "release" / "deps" / "libstandx.so",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        spec = importlib.util.spec_from_file_location("standx", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return None


def _build_standx_http_client(config: object) -> object | None:
    standx_backend = _import_standx_backend()
    if standx_backend is None:
        return None
    backend: Any = standx_backend

    is_testnet = bool(getattr(config, "is_testnet", False))
    base_url = getattr(config, "base_url_http", None) or (
        REST_URL_TESTNET if is_testnet else REST_URL_MAINNET
    )
    api_key = (
        getattr(config, "api_key", None)
        or os.getenv("STANDX_API_TOKEN")
        or os.getenv("STANDX_API_KEY")
    )
    api_secret = (
        getattr(config, "api_secret", None)
        or os.getenv("STANDX_REQUEST_ED25519_PRIVATE_KEY")
        or os.getenv("STANDX_API_SECRET")
    )

    if not api_key or not api_secret:
        return None

    return backend.PyStandXHttpClient(base_url, api_key, api_secret)


class StandXLiveDataClientFactory(LiveDataClientFactory):
    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LiveDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        typed_config = (
            config if isinstance(config, StandXDataClientConfig) else StandXDataClientConfig()
        )
        backend_client = _build_standx_http_client(typed_config)
        instrument_provider = StandXInstrumentProvider(client=backend_client)

        return StandXDataClient(
            loop=loop,
            client=backend_client,
            client_id=ClientId(name),
            venue=VENUE,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=instrument_provider,
            config=typed_config,
        )


class StandXLiveExecClientFactory(LiveExecClientFactory):
    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LiveExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        from nautilus_trader.model.enums import AccountType, OmsType

        typed_config = (
            config if isinstance(config, StandXExecClientConfig) else StandXExecClientConfig()
        )
        backend_client = _build_standx_http_client(typed_config)
        instrument_provider = StandXInstrumentProvider(client=backend_client)

        return StandXExecutionClient(
            loop=loop,
            client=backend_client,
            client_id=ClientId(name),
            venue=VENUE,
            oms_type=OmsType.NETTING,
            account_type=AccountType.MARGIN,
            base_currency=None,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=typed_config,
        )
