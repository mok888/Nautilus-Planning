import asyncio
from typing import Any

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogColor
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import NautilusConfig
from nautilus_trader.data.messages import SubscribeOrderBook
from nautilus_trader.data.messages import SubscribeQuoteTicks
from nautilus_trader.data.messages import SubscribeTradeTicks
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.model.data import BookOrder
from nautilus_trader.model.data import OrderBookDelta
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.enums import BookAction
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity

from .constants import WS_URL_PUBLIC


class LighterDataClient(LiveMarketDataClient):
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

    @staticmethod
    def _ns_from_ms(value: Any) -> int:
        try:
            return int(value) * 1_000_000
        except Exception:
            return 0

    def _resolve_instrument_id(self, msg: dict) -> InstrumentId | None:
        symbol = msg.get("symbol") or msg.get("market")
        if symbol is not None:
            upper = str(symbol).upper()
            if not upper.endswith("-USD-PERP"):
                if upper.endswith("PERP"):
                    upper = upper[:-4]
                upper = f"{upper}-USD-PERP"
            return InstrumentId.from_str(f"{upper}.{self.venue.value}")

        market_index = msg.get("market_index") or msg.get("market_id")
        if market_index is None:
            return None

        for instrument in self._instrument_provider.get_all().values():
            info = getattr(instrument, "info", None)
            if not isinstance(info, dict):
                continue
            info_market = info.get("market_id") or info.get("market_index")
            if info_market is None:
                continue
            if int(info_market) == int(market_index):
                return instrument.id
        return None

    async def _connect(self) -> None:
        self._log.info("Connecting to Lighter WebSocket...", LogColor.BLUE)
        if self._client is None:
            raise RuntimeError("Lighter data client backend is not configured")

        if hasattr(self._instrument_provider, "load_all_async"):
            await self._instrument_provider.load_all_async()
        self._send_all_instruments_to_data_engine()
        self._ws = self._client

    def _send_all_instruments_to_data_engine(self) -> None:
        for instrument in self._instrument_provider.get_all().values():
            self._handle_data(instrument)

        for currency in self._instrument_provider.currencies().values():
            self._cache.add_currency(currency)

    async def _disconnect(self) -> None:
        if self._ws is not None:
            self._log.info("Disconnecting from Lighter WebSocket...", LogColor.BLUE)

        if self._client is not None and hasattr(self._client, "close"):
            typed_client: Any = self._client
            close_result = typed_client.close()
            if asyncio.iscoroutine(close_result):
                await close_result

        self._ws = None

    async def _request(self, request) -> None:
        self._log.debug(f"Ignoring unsupported request command: {request}")

    async def _subscribe(self, command) -> None:
        self._log.debug(f"Generic subscribe command received: {command}")

    async def _subscribe_trade_ticks(self, command: SubscribeTradeTicks) -> None:
        symbol = command.instrument_id.symbol.value
        self._log.info(f"Subscribing to trades for {symbol}", LogColor.BLUE)
        client = self._client
        if client is not None and hasattr(client, "subscribe_trades"):
            typed_client: Any = client
            maybe = typed_client.subscribe_trades(symbol)
            if asyncio.iscoroutine(maybe):
                await maybe

    async def _subscribe_quote_ticks(self, command: SubscribeQuoteTicks) -> None:
        symbol = command.instrument_id.symbol.value
        self._log.info(f"Subscribing to quotes for {symbol}", LogColor.BLUE)

    async def _subscribe_order_book_deltas(self, command: SubscribeOrderBook) -> None:
        symbol = command.instrument_id.symbol.value
        self._log.info(f"Subscribing to orderbook for {symbol}", LogColor.BLUE)
        client = self._client
        if client is not None and hasattr(client, "subscribe_orderbook"):
            typed_client: Any = client
            maybe = typed_client.subscribe_orderbook(symbol)
            if asyncio.iscoroutine(maybe):
                await maybe

    async def _handle_ws_message(self, msg: dict) -> None:
        channel = msg.get("channel", "")
        if channel == "trades":
            self._handle_trade(msg)
        elif channel == "orderbook":
            self._handle_orderbook(msg)

    def _handle_trade(self, msg: dict) -> None:
        instrument_id = self._resolve_instrument_id(msg)
        if instrument_id is None:
            self._log.warning(f"Trade message skipped (unknown instrument): {msg}")
            return

        rows = msg.get("trades")
        if not isinstance(rows, list):
            rows = [msg]

        for row in rows:
            if not isinstance(row, dict):
                continue

            price_raw = row.get("price")
            size_raw = row.get("size")
            if size_raw is None:
                size_raw = row.get("quantity")

            if price_raw in (None, "") or size_raw in (None, ""):
                continue

            side = str(row.get("side") or "").upper()
            if side == "BUY":
                aggressor_side = AggressorSide.BUYER
            elif side == "SELL":
                aggressor_side = AggressorSide.SELLER
            else:
                aggressor_side = AggressorSide.NO_AGGRESSOR

            ts_event = self._ns_from_ms(row.get("timestamp") or msg.get("timestamp"))
            if ts_event == 0:
                ts_event = self._clock.timestamp_ns()

            trade_id_val = row.get("trade_id") or row.get("id") or f"{ts_event}"

            try:
                tick = TradeTick(
                    instrument_id=instrument_id,
                    price=Price.from_str(str(price_raw)),
                    size=Quantity.from_str(str(size_raw)),
                    aggressor_side=aggressor_side,
                    trade_id=TradeId(str(trade_id_val)),
                    ts_event=ts_event,
                    ts_init=self._clock.timestamp_ns(),
                )
            except Exception as exc:
                self._log.warning(f"Trade message parse error: {exc} ({row})")
                continue

            self._handle_data(tick)

    def _handle_orderbook(self, msg: dict) -> None:
        instrument_id = self._resolve_instrument_id(msg)
        if instrument_id is None:
            self._log.warning(f"Orderbook message skipped (unknown instrument): {msg}")
            return

        payload = msg.get("order_book") if isinstance(msg.get("order_book"), dict) else msg
        if not isinstance(payload, dict):
            return
        bids = payload.get("bids", []) if isinstance(payload, dict) else []
        asks = payload.get("asks", []) if isinstance(payload, dict) else []
        ts_event = self._ns_from_ms(payload.get("timestamp") if isinstance(payload, dict) else None)
        if ts_event == 0:
            ts_event = self._clock.timestamp_ns()
        sequence = int(payload.get("sequence") or msg.get("sequence") or 0)

        deltas: list[OrderBookDelta] = []

        for level in bids:
            price_raw = None
            size_raw = None
            if isinstance(level, (list, tuple)) and len(level) >= 2:
                price_raw, size_raw = level[0], level[1]
            elif isinstance(level, dict):
                price_raw = level.get("price")
                size_raw = level.get("size") or level.get("quantity")
            if price_raw in (None, "") or size_raw in (None, ""):
                continue
            try:
                order = BookOrder(
                    OrderSide.BUY,
                    Price.from_str(str(price_raw)),
                    Quantity.from_str(str(size_raw)),
                    0,
                )
                deltas.append(
                    OrderBookDelta(
                        instrument_id=instrument_id,
                        action=BookAction.UPDATE,
                        order=order,
                        flags=0,
                        sequence=sequence,
                        ts_event=ts_event,
                        ts_init=self._clock.timestamp_ns(),
                    ),
                )
            except Exception:
                continue

        for level in asks:
            price_raw = None
            size_raw = None
            if isinstance(level, (list, tuple)) and len(level) >= 2:
                price_raw, size_raw = level[0], level[1]
            elif isinstance(level, dict):
                price_raw = level.get("price")
                size_raw = level.get("size") or level.get("quantity")
            if price_raw in (None, "") or size_raw in (None, ""):
                continue
            try:
                order = BookOrder(
                    OrderSide.SELL,
                    Price.from_str(str(price_raw)),
                    Quantity.from_str(str(size_raw)),
                    0,
                )
                deltas.append(
                    OrderBookDelta(
                        instrument_id=instrument_id,
                        action=BookAction.UPDATE,
                        order=order,
                        flags=0,
                        sequence=sequence,
                        ts_event=ts_event,
                        ts_init=self._clock.timestamp_ns(),
                    ),
                )
            except Exception:
                continue

        if not deltas:
            best_bid = payload.get("best_bid") if isinstance(payload, dict) else None
            best_ask = payload.get("best_ask") if isinstance(payload, dict) else None
            bid_size = payload.get("best_bid_size") if isinstance(payload, dict) else None
            ask_size = payload.get("best_ask_size") if isinstance(payload, dict) else None
            if (
                best_bid not in (None, "")
                and best_ask not in (None, "")
                and bid_size not in (None, "")
                and ask_size not in (None, "")
            ):
                try:
                    quote = QuoteTick(
                        instrument_id=instrument_id,
                        bid_price=Price.from_str(str(best_bid)),
                        ask_price=Price.from_str(str(best_ask)),
                        bid_size=Quantity.from_str(str(bid_size)),
                        ask_size=Quantity.from_str(str(ask_size)),
                        ts_event=ts_event,
                        ts_init=self._clock.timestamp_ns(),
                    )
                    self._handle_data(quote)
                except Exception:
                    self._log.debug(f"Orderbook quote parse skipped: {payload}")
            return

        self._handle_data(OrderBookDeltas(instrument_id=instrument_id, deltas=deltas))
