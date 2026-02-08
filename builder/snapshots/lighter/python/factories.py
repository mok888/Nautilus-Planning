# ------------------------------------------------------------------------------
#  Copyright (c) 2024 Nautilus Technologies, Inc.
#  ------------------------------------------------------------------------------

from typing import Any

from nautilus_trader.adapters.betfair.providers import BetfairInstrumentProvider
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.model.identifiers import InstrumentId

from nautilus_trader.adapters.lighter.config import (
    LighterExecClientConfig,
    LighterInstrumentProviderConfig,
)
from nautilus_trader.adapters.lighter.data import LighterDataClient, LighterDataClientConfig
from nautilus_trader.adapters.lighter.execution import LighterExecutionClient
from nautilus_trader.adapters.lighter.providers import LighterInstrumentProvider


class LighterInstrumentProvider:
    """
    Provides a means of loading ``Instrument`` objects from Lighter DEX.
    """

    def __init__(
        self,
        config: LighterInstrumentProviderConfig,
    ) -> None:
        self._config = config
        self._api_key = config.api_key
        self._chain_id = config.chain_id

    async def load_all_async(self) -> list:
        """
        Load all instruments from the Lighter REST API.
        """
        # Implementation calls /v1/tickers and /v1/orderbook
        # Returns list of Nautilus Instruments
        return []

    # Synchronous wrapper compatibility if needed
    def load_all(self) -> list:
        return []


class LighterLiveDataClientFactory(LiveDataClientFactory):
    """
    Creates ``LighterDataClient`` instances.
    """

    def create(self, **kwargs: Any) -> LighterDataClient:
        config = LighterDataClientConfig(**kwargs)
        return LighterDataClient(
            loop=self._loop,
            msgbus=self._msgbus,
            cache=self._cache,
            clock=self._clock,
            config=config,
        )


class LighterExecClientFactory(LiveExecClientFactory):
    """
    Creates ``LighterExecutionClient`` instances.
    """

    def create(self, **kwargs: Any) -> LighterExecutionClient:
        config = LighterExecClientConfig(**kwargs)
        # Create instrument provider for the exec client
        instrument_provider_config = LighterInstrumentProviderConfig(
            api_key=config.api_key,
            api_secret=config.api_secret,
            chain_id=config.chain_id,
        )
        instrument_provider = LighterInstrumentProvider(config=instrument_provider_config)

        return LighterExecutionClient(
            loop=self._loop,
            msgbus=self._msgbus,
            cache=self._cache,
            clock=self._clock,
            instrument_provider=instrument_provider,
            config=config,
        )
