import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient

from .config import GrvtDataClientConfig, GrvtExecClientConfig
from .data import GrvtDataClient
from .execution import GrvtExecutionClient
from .constants import VENUE
from .providers import GrvtInstrumentProvider


class GrvtLiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating Grvt live data client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: GrvtDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        """
        Create a new GrvtDataClient instance.
        """
        instrument_provider = GrvtInstrumentProvider()

        return GrvtDataClient(
            loop=loop,
            client=None,
            client_id=name,
            venue=VENUE,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=instrument_provider,
            config=config,
        )


class GrvtLiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating Grvt live execution client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: GrvtExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        """
        Create a new GrvtExecutionClient instance.
        """
        from nautilus_trader.model.enums import OmsType, AccountType

        instrument_provider = GrvtInstrumentProvider()

        return GrvtExecutionClient(
            loop=loop,
            client=None,
            client_id=name,
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
