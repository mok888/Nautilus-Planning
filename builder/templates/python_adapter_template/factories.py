import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient

from .config import {{EXCHANGE_NAME}}DataClientConfig, {{EXCHANGE_NAME}}ExecutionClientConfig
from .data_client import {{EXCHANGE_NAME}}DataClient
from .execution_client import {{EXCHANGE_NAME}}ExecutionClient

class {{EXCHANGE_NAME}}LiveDataClientFactory(LiveDataClientFactory):
    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: {{EXCHANGE_NAME}}DataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveDataClient:
        return {{EXCHANGE_NAME}}DataClient(
            loop=loop,
            client_id=name,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
            # Pass other dependencies...
        )

class {{EXCHANGE_NAME}}LiveExecClientFactory(LiveExecClientFactory):
    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: {{EXCHANGE_NAME}}ExecutionClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> LiveExecutionClient:
        return {{EXCHANGE_NAME}}ExecutionClient(
            loop=loop,
            client_id=name,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
            # Pass other dependencies...
        )
