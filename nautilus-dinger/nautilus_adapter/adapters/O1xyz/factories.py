import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient

from .config import O1XyzDataClientConfig, O1XyzExecClientConfig
from .data import O1XyzDataClient
from .execution import O1XyzExecutionClient
from .constants import VENUE
from .providers import O1XyzInstrumentProvider


class O1XyzLiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating O1Xyz live data client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: O1XyzDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        """
        Create a new O1XyzDataClient instance.
        """
        instrument_provider = O1XyzInstrumentProvider()

        return O1XyzDataClient(
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


class O1XyzLiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating O1Xyz live execution client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: O1XyzExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        """
        Create a new O1XyzExecutionClient instance.
        """
        from nautilus_trader.model.enums import OmsType, AccountType

        instrument_provider = O1XyzInstrumentProvider()

        return O1XyzExecutionClient(
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
