import asyncio
import importlib
import os

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.config import LiveDataClientConfig, LiveExecClientConfig
from nautilus_trader.model.identifiers import ClientId

from .data import ParadexDataClient
from .execution import ParadexExecutionClient
from .constants import VENUE, REST_URL_MAINNET, REST_URL_TESTNET
from .providers import ParadexInstrumentProvider


def _build_paradex_http_client(config: object) -> object | None:
    try:
        paradex_backend = importlib.import_module("paradex")
    except Exception:
        return None

    is_testnet = bool(getattr(config, "is_testnet", False))
    base_url = getattr(config, "base_url_http", None) or (
        REST_URL_TESTNET if is_testnet else REST_URL_MAINNET
    )
    chain_id = os.getenv("PARADEX_CHAIN_ID")

    starknet_account = (
        getattr(config, "api_key", None)
        or os.getenv("PARADEX_STARKNET_ACCOUNT")
        or os.getenv("PARADEX_MAIN_ACCOUNT_L2_ADDRESS")
    )
    starknet_private_key = (
        getattr(config, "api_secret", None)
        or os.getenv("PARADEX_STARKNET_PRIVATE_KEY")
        or os.getenv("PARADEX_SUBKEY_PRIVATE_KEY")
    )

    if not starknet_account or not starknet_private_key:
        return None

    return paradex_backend.PyParadexHttpClient(
        base_url,
        chain_id,
        starknet_account,
        starknet_private_key,
    )


class ParadexLiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating Paradex live data client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LiveDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        """
        Create a new ParadexDataClient instance.
        """
        backend_client = _build_paradex_http_client(config)
        instrument_provider = ParadexInstrumentProvider(client=backend_client)

        return ParadexDataClient(
            loop=loop,
            client=backend_client,
            client_id=ClientId(name),
            venue=VENUE,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=instrument_provider,
            config=config,
        )


class ParadexLiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating Paradex live execution client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LiveExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        """
        Create a new ParadexExecutionClient instance.
        """
        from nautilus_trader.model.enums import OmsType, AccountType

        backend_client = _build_paradex_http_client(config)
        instrument_provider = ParadexInstrumentProvider(client=backend_client)

        return ParadexExecutionClient(
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
            config=config,
        )
