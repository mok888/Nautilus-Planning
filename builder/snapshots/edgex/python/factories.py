import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient

from .config import EdgexDataClientConfig, EdgexExecClientConfig
from .data import EdgexDataClient
from .execution import EdgexExecutionClient
from .constants import VENUE
from .providers import EdgexInstrumentProvider


class EdgexLiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating Edgex live data client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: EdgexDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        """
        Create a new EdgexDataClient instance.
        """
        instrument_provider = EdgexInstrumentProvider()

        return EdgexDataClient(
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


class EdgexLiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating Edgex live execution client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: EdgexExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        """
        Create a new EdgexExecutionClient instance.
        """
        from nautilus_trader.model.enums import OmsType, AccountType

        instrument_provider = EdgexInstrumentProvider()

        return EdgexExecutionClient(
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
