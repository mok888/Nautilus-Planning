# ------------------------------------------------------------------------------
#  Copyright (c) 2024 Nautilus Technologies, Inc.
#  ------------------------------------------------------------------------------

from typing import Any

import msgspec

from nautilus_trader.adapters.http.client import HttpClient
from nautilus_trader.common.clock import LiveClock
from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.core.data import Data
from nautilus_trader.live.data_client import LiveDataProvider
from nautilus_trader.model.data import OrderBookDeltas, QuoteTick, TradeTick
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.msgbus.bus import MessageBus

from nautilus_trader.adapters.lighter.constants import (
    LIGHTER_REST_BASE_URL,
    LIGHTER_VENUE,
    LIGHTER_WS_PUBLIC_URL,
)
from nautilus_trader.adapters.lighter.types import LighterOrderBookMsg, LighterTradeMsg


class LighterDataClientConfig(LiveDataClientConfig, kw_only=True):
    """
    Configuration for ``LighterDataClient``.

    Parameters
    ----------
    chain_id : str, default "137"
        The blockchain chain ID.
    """

    chain_id: str = "137"


class LighterDataClient(LiveDataProvider):
    """
    Provides a live data connection for Lighter DEX.
    """

    def __init__(
        self,
        loop: Any,
        msgbus: MessageBus,
        cache: Any,
        clock: LiveClock,
        config: LighterDataClientConfig,
    ) -> None:
        PyCondition.type(config, LighterDataClientConfig, "config")
        super().__init__(
            loop=loop,
            client_id=LighterDataClient.__name__,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
        )

        self._config: LighterDataClientConfig = config
        self._chain_id: str = config.chain_id
        self._http_client: HttpClient = HttpClient(base_url=LIGHTER_REST_BASE_URL)
        self._decoder = msgspec.json.Decoder(LighterOrderBookMsg)
        self._trade_decoder = msgspec.json.Decoder(LighterTradeMsg)

        self._log.info(f"Initializing Lighter Data Client (chain_id={self._chain_id}).")

    async def _connect(self) -> None:
        # Implementation of WebSocket connection logic would go here
        # Connecting to LIGHTER_WS_PUBLIC_URL
        self._log.info("Connecting to Lighter WebSocket...")
        self._set_connected(True)

    async def _disconnect(self) -> None:
        self._log.info("Disconnecting Lighter Data Client...")
        self._set_connected(False)

    async def _subscribe_instrument(self, instrument_id: InstrumentId) -> None:
        self._log.info(f"Subscribing to instrument {instrument_id}.")
        # Logic to send subscription message to WS

    async def _subscribe_instruments(self) -> None:
        self._log.info("Subscribing to all instruments.")

    async def _subscribe_order_book_deltas(self, instrument_id: InstrumentId) -> None:
        self._log.info(f"Subscribing to OrderBookDeltas for {instrument_id}.")
        # Subscribe to 'orderbook' channel

    async def _subscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        self._log.info(f"Subscribing to QuoteTicks for {instrument_id}.")

    async def _subscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        self._log.info(f"Subscribing to TradeTicks for {instrument_id}.")
        # Subscribe to 'trades' channel

    # Internal methods to parse incoming WS data
    def _process_order_book(self, raw: bytes) -> None:
        msg = self._decoder.decode(raw)
        # Convert Nautilus OrderBookDeltas
        # self._msgbus.publish(topic=..., msg=...)

    def _process_trade(self, raw: bytes) -> None:
        msg = self._trade_decoder.decode(raw)
        # Convert Nautilus TradeTick
        # self._msgbus.publish(topic=..., msg=...)
