import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient

from .config import LighterDataClientConfig, LighterExecutionClientConfig
from .data_client import LighterDataClient
from .execution_client import LighterExecutionClient

class LighterLiveDataClientFactory(LiveDataClientFactory):
    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LighterDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        return LighterDataClient(
            loop=loop,
            client_id=name,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
            # Pass other dependencies...
        )

class LighterLiveExecClientFactory(LiveExecClientFactory):
    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LighterExecutionClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        return LighterExecutionClient(
            loop=loop,
            client_id=name,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
            # Pass other dependencies...
        )
