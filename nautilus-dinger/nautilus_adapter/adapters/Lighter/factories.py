import asyncio
import os

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.config import LiveDataClientConfig, LiveExecClientConfig
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.model.identifiers import ClientId

from .backend import LighterSdkBackend
from .config import LighterDataClientConfig, LighterExecClientConfig
from .constants import REST_URL_MAINNET, REST_URL_TESTNET, VENUE
from .data import LighterDataClient
from .execution import LighterExecutionClient
from .providers import LighterInstrumentProvider


def _build_lighter_backend(config: object) -> LighterSdkBackend | None:
    is_testnet = bool(getattr(config, "is_testnet", False))
    base_url = getattr(config, "base_url_http", None) or (
        REST_URL_TESTNET if is_testnet else REST_URL_MAINNET
    )

    account_index = getattr(config, "account_index", None) or os.getenv("LIGHTER_ACCOUNT_INDEX")
    api_key_index = getattr(config, "api_key", None) or os.getenv("LIGHTER_API_KEY_INDEX")
    api_private_key = (
        getattr(config, "api_secret", None)
        or os.getenv("LIGHTER_API_SECRET")
        or os.getenv("LIGHTER_API_KEY_PRIVATE_KEY")
    )

    if not account_index or not api_key_index or not api_private_key:
        return None

    return LighterSdkBackend(
        base_url=base_url,
        account_index=int(account_index),
        api_key_index=int(api_key_index),
        api_key_private_key=str(api_private_key),
    )


class LighterLiveDataClientFactory(LiveDataClientFactory):
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
            config if isinstance(config, LighterDataClientConfig) else LighterDataClientConfig()
        )
        backend_client = _build_lighter_backend(typed_config)
        instrument_provider = LighterInstrumentProvider(client=backend_client)

        return LighterDataClient(
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


class LighterLiveExecClientFactory(LiveExecClientFactory):
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
            config if isinstance(config, LighterExecClientConfig) else LighterExecClientConfig()
        )
        backend_client = _build_lighter_backend(typed_config)
        instrument_provider = LighterInstrumentProvider(client=backend_client)

        return LighterExecutionClient(
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
