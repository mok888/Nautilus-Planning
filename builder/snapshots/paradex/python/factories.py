import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient

from .config import ParadexDataClientConfig, ParadexExecClientConfig
from .data import ParadexDataClient
from .execution import ParadexExecutionClient
from .constants import VENUE
from .providers import ParadexInstrumentProvider


class ParadexLiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating Paradex live data client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: ParadexDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        """
        Create a new ParadexDataClient instance.
        """
        instrument_provider = ParadexInstrumentProvider()

        return ParadexDataClient(
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


class ParadexLiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating Paradex live execution client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: ParadexExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        """
        Create a new ParadexExecutionClient instance.
        """
        from nautilus_trader.model.enums import OmsType, AccountType

        instrument_provider = ParadexInstrumentProvider()

        return ParadexExecutionClient(
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
