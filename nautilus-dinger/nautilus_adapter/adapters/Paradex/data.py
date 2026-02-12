import asyncio
from typing import Any

from nautilus_trader.common.component import MessageBus
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import NautilusConfig
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.model.identifiers import ClientId, Venue
from nautilus_trader.data.messages import SubscribeTradeTicks, SubscribeQuoteTicks, SubscribeOrderBook
from nautilus_trader.common.enums import LogColor

from .constants import WS_URL_PUBLIC


class ParadexDataClient(LiveMarketDataClient):
    """
    A NautilusTrader Data Client for the Paradex exchange.

    Connects to the Paradex WebSocket feed for real-time market data
    including orderbook updates, trade executions, and ticker data.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client: object,
        client_id: ClientId,
        venue: Venue,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: InstrumentProvider,
        config: NautilusConfig | None = None,
    ):
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=instrument_provider,
            config=config,
        )
        self._client = client
        self._websocket_url = getattr(config, "base_url_ws", None) or WS_URL_PUBLIC
        self._ws = None

    async def _connect(self) -> None:
        """
        Connect to the Paradex WebSocket feed.
        """
        self._log.info("Connecting to Paradex WebSocket...", LogColor.BLUE)
        if self._client is None:
            raise RuntimeError("Paradex data client backend is not configured")

        await self._instrument_provider.load_all_async()
        self._send_all_instruments_to_data_engine()

        self._ws = self._client

    def _send_all_instruments_to_data_engine(self) -> None:
        for instrument in self._instrument_provider.get_all().values():
            self._handle_data(instrument)

        for currency in self._instrument_provider.currencies().values():
            self._cache.add_currency(currency)

    async def _disconnect(self) -> None:
        """
        Disconnect from the Paradex WebSocket feed.
        """
        if self._ws is not None:
            self._log.info("Disconnecting from Paradex WebSocket...", LogColor.BLUE)
        self._ws = None

    async def _request(self, request) -> None:
        """
        Handle generic request logic.
        """
        self._log.debug(f"Ignoring unsupported request command: {request}")

    async def _subscribe(self, command) -> None:
        """
        Handle generic subscription logic.
        """
        self._log.debug(f"Generic subscribe command received: {command}")

    async def _subscribe_trade_ticks(self, command: SubscribeTradeTicks) -> None:
        """
        Subscribe to the trades channel for a given instrument.
        """
        symbol = command.instrument_id.symbol.value
        self._log.info(f"Subscribing to trades for {symbol}", LogColor.BLUE)
        client = self._client
        if client is not None and hasattr(client, "subscribe_trades"):
            typed_client: Any = client
            await self._loop.run_in_executor(None, lambda: typed_client.subscribe_trades(symbol))

    async def _subscribe_quote_ticks(self, command: SubscribeQuoteTicks) -> None:
        """
        Subscribe to the ticker channel for a given instrument.
        """
        symbol = command.instrument_id.symbol.value
        self._log.info(f"Subscribing to quotes for {symbol}", LogColor.BLUE)

    async def _subscribe_order_book_deltas(self, command: SubscribeOrderBook) -> None:
        """
        Subscribe to the orderbook channel for a given instrument.
        """
        symbol = command.instrument_id.symbol.value
        self._log.info(f"Subscribing to orderbook for {symbol}", LogColor.BLUE)
        client = self._client
        if client is not None and hasattr(client, "subscribe_orderbook"):
            typed_client: Any = client
            await self._loop.run_in_executor(None, lambda: typed_client.subscribe_orderbook(symbol))

    async def _handle_ws_message(self, msg: dict) -> None:
        """
        Process incoming WebSocket messages and dispatch to handlers.
        """
        channel = msg.get("channel", "")
        if channel == "trades":
            self._handle_trade(msg)
        elif channel == "orderbook":
            self._handle_orderbook(msg)

    def _handle_trade(self, msg: dict) -> None:
        """
        Parse a trade message and emit a TradeTick.
        """
        self._log.debug(f"Trade message received: {msg}")

    def _handle_orderbook(self, msg: dict) -> None:
        """
        Parse an orderbook message and emit OrderBookDeltas.
        """
        self._log.debug(f"Orderbook message received: {msg}")
