import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient

from .config import NadoDataClientConfig, NadoExecClientConfig
from .data import NadoDataClient
from .execution import NadoExecutionClient
from .constants import VENUE
from .providers import NadoInstrumentProvider


class NadoLiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating Nado live data client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: NadoDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        """
        Create a new NadoDataClient instance.
        """
        instrument_provider = NadoInstrumentProvider()

        return NadoDataClient(
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


class NadoLiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating Nado live execution client instances.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: NadoExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        """
        Create a new NadoExecutionClient instance.
        """
        from nautilus_trader.model.enums import OmsType, AccountType

        instrument_provider = NadoInstrumentProvider()

        return NadoExecutionClient(
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
