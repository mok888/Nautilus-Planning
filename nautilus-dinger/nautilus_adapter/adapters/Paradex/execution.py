import asyncio
import json
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any

from nautilus_trader.common.component import MessageBus
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import NautilusConfig
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientId, ClientOrderId, Venue
from nautilus_trader.model.identifiers import InstrumentId, TradeId
from nautilus_trader.model.enums import (
    OmsType,
    AccountType,
    OrderStatus,
    OrderType,
    TimeInForce,
    LiquiditySide,
    OrderSide,
    TriggerType,
)
from nautilus_trader.model.objects import AccountBalance, Currency, MarginBalance, Money, Price, Quantity
from nautilus_trader.execution.messages import (
    SubmitOrder,
    SubmitOrderList,
    CancelOrder,
    CancelAllOrders,
    BatchCancelOrders,
    ModifyOrder,
)
from nautilus_trader.execution.reports import (
    OrderStatusReport,
    FillReport,
    PositionStatusReport,
    ExecutionMassStatus,
)
from nautilus_trader.common.enums import LogColor
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.core.uuid import UUID4

from .constants import WS_URL_PRIVATE, REST_URL_MAINNET, REST_URL_TESTNET


class ParadexExecutionClient(LiveExecutionClient):
    """
    A NautilusTrader Execution Client for the Paradex exchange.

    Handles order submission, cancellation, and position management
    via the Paradex REST API and WebSocket private feed.
    Orders are submitted as stark_ecdsa transactions via the /action endpoint.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client: object,
        client_id: ClientId,
        venue: Venue,
        oms_type: OmsType,
        account_type: AccountType,
        base_currency: Currency | None,
        instrument_provider: InstrumentProvider,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        config: NautilusConfig | None = None,
    ):
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            oms_type=oms_type,
            account_type=account_type,
            base_currency=base_currency,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
        )
        self._client = client
        is_testnet = bool(getattr(config, "is_testnet", False)) if config is not None else False
        self._base_url = (
            getattr(config, "base_url_http", None)
            or (REST_URL_TESTNET if is_testnet else REST_URL_MAINNET)
        )
        self._ws_url = getattr(config, "base_url_ws", None) or WS_URL_PRIVATE
        configured_lookback = getattr(config, "reconciliation_lookback_mins", None) if config is not None else None
        self._reconciliation_lookback_mins = int(configured_lookback) if configured_lookback is not None else 120
        configured_page_size = getattr(config, "reconciliation_page_size", 100) if config is not None else 100
        self._reconciliation_page_size = max(1, min(int(configured_page_size), 200))
        self._set_account_id(AccountId(f"{venue.value}-001"))

    def _require_client(self) -> Any:
        if self._client is None:
            raise RuntimeError("Paradex execution client backend is not configured")
        return self._client

    @staticmethod
    def _ns_from_ms(value: Any) -> int:
        try:
            return int(value) * 1_000_000
        except Exception:
            return 0

    @staticmethod
    def _ms_from_datetime(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        if hasattr(value, "timestamp"):
            try:
                return int(value.timestamp() * 1000)
            except Exception:
                return None
        return None

    @staticmethod
    def _parse_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
        try:
            return Decimal(str(value))
        except Exception:
            return default

    @staticmethod
    def _map_tif(value: str | None) -> TimeInForce:
        tif = (value or "GTC").upper()
        if tif == "IOC":
            return TimeInForce.IOC
        return TimeInForce.GTC

    @staticmethod
    def _map_order_type_from_venue(value: str | None) -> OrderType:
        t = (value or "LIMIT").upper()
        if t == "MARKET":
            return OrderType.MARKET
        if t == "STOP_MARKET":
            return OrderType.STOP_MARKET
        if t == "STOP_LIMIT":
            return OrderType.STOP_LIMIT
        if t == "TAKE_PROFIT_LIMIT":
            return OrderType.LIMIT_IF_TOUCHED
        if t == "TAKE_PROFIT_MARKET":
            return OrderType.MARKET_IF_TOUCHED
        if t == "STOP_LOSS_MARKET":
            return OrderType.STOP_MARKET
        if t == "STOP_LOSS_LIMIT":
            return OrderType.STOP_LIMIT
        return OrderType.LIMIT

    @classmethod
    def _map_order_status_from_venue(cls, venue_order: dict[str, Any]) -> OrderStatus:
        status = str(venue_order.get("status", "OPEN")).upper()
        size = cls._parse_decimal(venue_order.get("size"))
        remaining = cls._parse_decimal(venue_order.get("remaining_size"), size)
        filled = size - remaining if size >= remaining else Decimal("0")

        if status == "CLOSED":
            if remaining <= Decimal("0") and size > Decimal("0"):
                return OrderStatus.FILLED
            return OrderStatus.CANCELED
        if status in {"OPEN", "UNTRIGGERED", "NEW"}:
            if filled > Decimal("0"):
                return OrderStatus.PARTIALLY_FILLED
            return OrderStatus.ACCEPTED
        return OrderStatus.ACCEPTED

    @staticmethod
    def _map_liquidity(value: str | None) -> LiquiditySide:
        side = (value or "").upper()
        if side == "MAKER":
            return LiquiditySide.MAKER
        if side == "TAKER":
            return LiquiditySide.TAKER
        return LiquiditySide.NO_LIQUIDITY_SIDE

    @staticmethod
    def _map_order_side(value: str | None) -> OrderSide:
        side = (value or "BUY").upper()
        if side == "SELL":
            return OrderSide.SELL
        return OrderSide.BUY

    @staticmethod
    def _map_trigger_type(value: str | None) -> TriggerType:
        trigger = (value or "").upper()
        if trigger in {"MARK_PRICE", "MARK"}:
            return TriggerType.MARK_PRICE
        if trigger in {"INDEX_PRICE", "INDEX"}:
            return TriggerType.INDEX_PRICE
        if trigger in {"LAST_PRICE", "LAST"}:
            return TriggerType.LAST_PRICE
        return TriggerType.DEFAULT

    def _instrument_id_from_market(self, market: str | None) -> InstrumentId | None:
        if not market:
            return None
        try:
            return InstrumentId.from_str(f"{market}.{self.venue.value}")
        except Exception:
            return None

    async def _connect(self) -> None:
        """
        Connect to the Paradex execution interface.
        """
        self._log.info("Connecting to Paradex execution...", LogColor.BLUE)
        client = self._require_client()
        def _probe_connection() -> object:
            if hasattr(client, "get_timestamp"):
                return client.get_timestamp()
            if hasattr(client, "get_info"):
                return client.get_info()
            raise RuntimeError("Paradex backend missing connectivity probe method")

        await self._loop.run_in_executor(None, _probe_connection)
        if hasattr(client, "set_account_id"):
            await self._loop.run_in_executor(None, lambda: client.set_account_id(str(self.account_id)))
        await self._instrument_provider.load_all_async()
        for instrument in self._instrument_provider.get_all().values():
            self._cache.add_instrument(instrument)
        for currency in self._instrument_provider.currencies().values():
            self._cache.add_currency(currency)
        await self._update_account_state()
        await self._await_account_registered()

    async def _update_account_state(self) -> None:
        currency = Currency.from_str("USDC")
        zero_money = Money(0, currency)
        self.generate_account_state(
            balances=[
                AccountBalance(
                    total=zero_money,
                    locked=zero_money,
                    free=zero_money,
                ),
            ],
            margins=[
                MarginBalance(
                    initial=zero_money,
                    maintenance=zero_money,
                    instrument_id=None,
                ),
            ],
            reported=True,
            ts_event=self._clock.timestamp_ns(),
        )

    async def _disconnect(self) -> None:
        """
        Disconnect from the Paradex execution interface.
        """
        self._log.info("Disconnecting from Paradex execution...", LogColor.BLUE)
        return None

    async def _submit_order(self, command: SubmitOrder) -> None:
        """
        Submit an order to Paradex via the /action endpoint.

        Orders are submitted as stark_ecdsa transactions signed with Ed25519.
        """
        self._log.info(
            f"Submitting {command.order.type_string()} order for "
            f"{command.instrument_id}",
            LogColor.BLUE,
        )
        await self._submit_single_order(
            strategy_id=command.strategy_id,
            instrument_id=command.instrument_id,
            order=command.order,
        )

    @staticmethod
    def _order_has_tag(order: Any, tag: str) -> bool:
        tags = getattr(order, "tags", None)
        if tags is None:
            return False
        return any(str(t).upper() == tag.upper() for t in tags)

    @classmethod
    def _map_order_type(cls, order: Any) -> str:
        if order.is_reduce_only and cls._order_has_tag(order, "TAKE_PROFIT"):
            if order.has_trigger_price:
                return "TAKE_PROFIT_MARKET" if not order.has_price else "TAKE_PROFIT_LIMIT"
            return "TAKE_PROFIT_LIMIT" if order.has_price else "TAKE_PROFIT_MARKET"

        if order.is_reduce_only and cls._order_has_tag(order, "STOP_LOSS"):
            if order.has_trigger_price:
                return "STOP_LOSS_MARKET" if not order.has_price else "STOP_LOSS_LIMIT"
            return "STOP_LOSS_LIMIT" if order.has_price else "STOP_LOSS_MARKET"

        order_type = order.type_string().upper()
        if order_type == "LIMIT_IF_TOUCHED":
            return "TAKE_PROFIT_LIMIT"
        if order_type == "MARKET_IF_TOUCHED":
            return "TAKE_PROFIT_MARKET"
        if order_type == "STOP_LIMIT" and order.is_reduce_only:
            return "STOP_LOSS_LIMIT"
        if order_type == "STOP_MARKET" and order.is_reduce_only:
            return "STOP_LOSS_MARKET"
        return order_type

    async def _submit_single_order(self, strategy_id: Any, instrument_id: Any, order: Any) -> None:
        client = self._require_client()
        ts_event = self._clock.timestamp_ns()

        order_type = self._map_order_type(order)
        side = order.side_string().upper()
        size = str(order.quantity)
        price = str(order.price) if order.has_price else "0"
        trigger_price = str(order.trigger_price) if order.has_trigger_price else None
        if trigger_price is None and order_type in {"TAKE_PROFIT_LIMIT", "STOP_LOSS_LIMIT"} and order.has_price:
            trigger_price = price
        instruction = order.tif_string().upper() if hasattr(order, "tif_string") else "GTC"
        client_order_id = str(order.client_order_id)

        self._log.debug(
            f"Mapped leg {client_order_id} to venue_type={order_type} "
            f"trigger_price={trigger_price} reduce_only={order.is_reduce_only}",
        )

        self.generate_order_submitted(
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            client_order_id=order.client_order_id,
            ts_event=ts_event,
        )

        try:
            result = await self._loop.run_in_executor(
                None,
                lambda: client.submit_order(
                    instrument_id.symbol.value,
                    side,
                    order_type,
                    size,
                    price,
                    client_order_id,
                    instruction,
                    trigger_price,
                    order.is_reduce_only,
                    None,
                ),
            )

            venue_order_id = None
            if isinstance(result, str):
                try:
                    payload = json.loads(result)
                    venue_id = payload.get("action_id") or payload.get("id")
                    if venue_id:
                        venue_order_id = VenueOrderId(str(venue_id))
                except json.JSONDecodeError:
                    venue_order_id = None

            if venue_order_id is not None:
                self.generate_order_accepted(
                    strategy_id=strategy_id,
                    instrument_id=instrument_id,
                    client_order_id=order.client_order_id,
                    venue_order_id=venue_order_id,
                    ts_event=self._clock.timestamp_ns(),
                )
            else:
                self.generate_order_rejected(
                    strategy_id=strategy_id,
                    instrument_id=instrument_id,
                    client_order_id=order.client_order_id,
                    reason="Venue response missing order identifier",
                    ts_event=self._clock.timestamp_ns(),
                )
        except Exception as e:
            self.generate_order_rejected(
                strategy_id=strategy_id,
                instrument_id=instrument_id,
                client_order_id=order.client_order_id,
                reason=str(e),
                ts_event=self._clock.timestamp_ns(),
            )

    async def _cancel_order(self, command: CancelOrder) -> None:
        """
        Cancel an order at Paradex via the /action endpoint.
        """
        self._log.info(
            f"Canceling order {command.client_order_id}",
            LogColor.BLUE,
        )
        client = self._require_client()
        market = command.instrument_id.symbol.value if command.instrument_id is not None else None

        def _is_not_found_error(exc: Exception) -> bool:
            message = str(exc).upper()
            return (
                "ORDER_ID_NOT_FOUND" in message
                or "CLIENT_ORDER_ID_NOT_FOUND" in message
                or "404" in message
            )

        try:
            try:
                await self._loop.run_in_executor(
                    None,
                    lambda: client.cancel_order_by_client_id(str(command.client_order_id), market),
                )
            except Exception:
                venue_order_id = str(command.venue_order_id) if command.venue_order_id is not None else None
                if venue_order_id is None or not hasattr(client, "cancel_order"):
                    raise
                await self._loop.run_in_executor(
                    None,
                    lambda: client.cancel_order(venue_order_id),
                )
            self.generate_order_canceled(
                strategy_id=command.strategy_id,
                instrument_id=command.instrument_id,
                client_order_id=command.client_order_id,
                venue_order_id=command.venue_order_id,
                ts_event=self._clock.timestamp_ns(),
            )
        except Exception as e:
            if _is_not_found_error(e):
                self._log.warning(
                    f"Cancel returned not-found for {command.client_order_id}; "
                    "treating as already terminal",
                )
                self.generate_order_canceled(
                    strategy_id=command.strategy_id,
                    instrument_id=command.instrument_id,
                    client_order_id=command.client_order_id,
                    venue_order_id=command.venue_order_id,
                    ts_event=self._clock.timestamp_ns(),
                )
                return
            self.generate_order_cancel_rejected(
                strategy_id=command.strategy_id,
                instrument_id=command.instrument_id,
                client_order_id=command.client_order_id,
                venue_order_id=command.venue_order_id,
                reason=str(e),
                ts_event=self._clock.timestamp_ns(),
            )

    async def _cancel_all_orders(self, command: CancelAllOrders) -> None:
        """
        Cancel all open orders for an instrument.
        """
        client = self._require_client()
        instrument_id = getattr(command, "instrument_id", None)
        market = instrument_id.symbol.value if instrument_id is not None else None
        if hasattr(client, "cancel_all_orders"):
            try:
                await self._loop.run_in_executor(None, lambda: client.cancel_all_orders(market))
            except Exception as exc:
                self._log.warning(f"Venue cancel_all failed: {exc}; falling back to local cancel loop")

        strategy_id = getattr(command, "strategy_id", None)
        order_side = getattr(command, "order_side", None)
        try:
            open_orders = self._cache.orders_open(
                venue=self.venue,
                instrument_id=instrument_id,
                strategy_id=strategy_id,
                side=order_side,
            )
        except Exception:
            open_orders = self._cache.orders_open(venue=self.venue, instrument_id=instrument_id)

        for order in open_orders:
            cancel_command = CancelOrder(
                trader_id=command.trader_id,
                strategy_id=command.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                venue_order_id=order.venue_order_id,
                command_id=UUID4(),
                ts_init=self._clock.timestamp_ns(),
                client_id=command.client_id,
                params=command.params,
                correlation_id=command.correlation_id,
            )
            await self._cancel_order(cancel_command)

    async def _modify_order(self, command: ModifyOrder) -> None:
        client = self._require_client()
        if not hasattr(client, "modify_order"):
            self.generate_order_modify_rejected(
                strategy_id=command.strategy_id,
                instrument_id=command.instrument_id,
                client_order_id=command.client_order_id,
                venue_order_id=command.venue_order_id,
                reason="Modify order is not available in Paradex client build",
                ts_event=self._clock.timestamp_ns(),
            )
            return

        def _is_order_not_open_error(exc: Exception) -> bool:
            text = str(exc).upper()
            return "ORDER_IS_NOT_OPEN" in text or "CANNOT BE MODIFIED" in text

        try:
            existing_raw = await self._loop.run_in_executor(
                None,
                lambda: client.get_order_by_id(str(command.venue_order_id))
                if command.venue_order_id is not None
                else client.get_order_by_client_id(str(command.client_order_id)),
            )
            existing = json.loads(existing_raw) if isinstance(existing_raw, str) else existing_raw
            if not isinstance(existing, dict):
                raise RuntimeError("Unexpected modify lookup payload")

            order_id = str(existing.get("id") or command.venue_order_id or "")
            market = str(existing.get("market") or command.instrument_id.symbol.value)
            side = str(existing.get("side") or "BUY")
            order_type = str(existing.get("type") or "LIMIT")

            size = (
                str(command.quantity)
                if command.quantity is not None
                else str(existing.get("size") or "0")
            )
            price = (
                str(command.price)
                if command.price is not None
                else str(existing.get("price") or "0")
            )
            trigger_price = (
                str(command.trigger_price)
                if command.trigger_price is not None
                else (
                    str(existing.get("trigger_price"))
                    if existing.get("trigger_price") not in (None, "")
                    else None
                )
            )
            if order_type.upper() not in {
                "STOP_LIMIT",
                "STOP_MARKET",
                "STOP_LOSS_LIMIT",
                "STOP_LOSS_MARKET",
                "TAKE_PROFIT_LIMIT",
                "TAKE_PROFIT_MARKET",
            }:
                trigger_price = None

            def _call_modify() -> Any:
                return client.modify_order(
                    order_id,
                    market,
                    side,
                    order_type,
                    size,
                    price,
                    trigger_price,
                    None,
                )

            try:
                modified_raw = await self._loop.run_in_executor(None, _call_modify)
            except Exception as first_error:
                if not _is_order_not_open_error(first_error):
                    raise

                latest_raw = await self._loop.run_in_executor(
                    None,
                    lambda: client.get_order_by_id(order_id),
                )
                latest = json.loads(latest_raw) if isinstance(latest_raw, str) else latest_raw
                latest_status = str(latest.get("status", "")).upper() if isinstance(latest, dict) else ""
                if latest_status in {"NEW", "UNTRIGGERED"}:
                    await asyncio.sleep(0.25)
                    modified_raw = await self._loop.run_in_executor(None, _call_modify)
                else:
                    raise

            modified = json.loads(modified_raw) if isinstance(modified_raw, str) else modified_raw
            if not isinstance(modified, dict):
                raise RuntimeError("Unexpected modify response payload")

            updated_venue_order_id = VenueOrderId(str(modified.get("id") or order_id))
            venue_order_id_modified = (
                command.venue_order_id is not None
                and str(updated_venue_order_id) != str(command.venue_order_id)
            )

            updated_qty = command.quantity
            if updated_qty is None:
                updated_qty = Quantity.from_str(size)

            updated_price = command.price
            if updated_price is None and price not in (None, ""):
                updated_price = Price.from_str(price)

            updated_trigger = command.trigger_price
            if updated_trigger is None and trigger_price not in (None, ""):
                updated_trigger = Price.from_str(str(trigger_price))

            self.generate_order_updated(
                strategy_id=command.strategy_id,
                instrument_id=command.instrument_id,
                client_order_id=command.client_order_id,
                venue_order_id=updated_venue_order_id,
                quantity=updated_qty,
                price=updated_price,
                trigger_price=updated_trigger,
                ts_event=self._clock.timestamp_ns(),
                venue_order_id_modified=venue_order_id_modified,
            )
        except Exception as e:
            self.generate_order_modify_rejected(
                strategy_id=command.strategy_id,
                instrument_id=command.instrument_id,
                client_order_id=command.client_order_id,
                venue_order_id=command.venue_order_id,
                reason=str(e),
                ts_event=self._clock.timestamp_ns(),
            )

    async def _batch_cancel_orders(self, command: BatchCancelOrders) -> None:
        """
        Batch cancel orders.
        """
        for cancel_command in command.cancels:
            await self._cancel_order(cancel_command)

    def _build_order_status_report_from_venue(self, venue_order: dict[str, Any]) -> OrderStatusReport | None:
        order_id = venue_order.get("id")
        market = venue_order.get("market")
        instrument_id = self._instrument_id_from_market(market)
        if not order_id or instrument_id is None:
            return None

        size = self._parse_decimal(venue_order.get("size"))
        remaining = self._parse_decimal(venue_order.get("remaining_size"), size)
        filled = size - remaining if size >= remaining else Decimal("0")
        venue_status = self._map_order_status_from_venue(venue_order)

        client_order_id = venue_order.get("client_id")
        cached_order = None
        if client_order_id is not None:
            try:
                cached_order = self._cache.order(ClientOrderId(str(client_order_id)))
            except Exception:
                cached_order = None
        if cached_order is None:
            try:
                cache_client_id = self._cache.client_order_id(VenueOrderId(str(order_id)))
                if cache_client_id is not None:
                    cached_order = self._cache.order(cache_client_id)
            except Exception:
                cached_order = None

        if cached_order is not None and cached_order.status != venue_status:
            self._log.warning(
                f"Order status mismatch for {order_id}: cache={cached_order.status_string()} venue={venue_status.name}",
            )

        try:
            qty = Quantity.from_str(str(size))
            filled_qty = Quantity.from_str(str(filled))
        except Exception:
            return None

        price_val = venue_order.get("price")
        trigger_val = venue_order.get("trigger_price")
        avg_fill_val = venue_order.get("avg_fill_price")
        price = Price.from_str(str(price_val)) if price_val not in (None, "") else None
        trigger_price = Price.from_str(str(trigger_val)) if trigger_val not in (None, "") else None
        trigger_type = self._map_trigger_type(venue_order.get("trigger_type")) if trigger_price is not None else TriggerType.NO_TRIGGER
        avg_px = self._parse_decimal(avg_fill_val) if avg_fill_val not in (None, "") else None

        ts_init = self._ns_from_ms(venue_order.get("created_at")) or self._clock.timestamp_ns()
        ts_last = self._ns_from_ms(venue_order.get("last_updated_at")) or ts_init

        report_client_order_id = cached_order.client_order_id if cached_order is not None else None
        if report_client_order_id is not None:
            try:
                report_client_order_id = ClientOrderId(str(report_client_order_id))
            except Exception:
                report_client_order_id = None
        if report_client_order_id is None and client_order_id is not None:
            try:
                report_client_order_id = ClientOrderId(str(client_order_id))
            except Exception:
                report_client_order_id = None

        return OrderStatusReport(
            account_id=self.account_id,
            instrument_id=instrument_id,
            venue_order_id=VenueOrderId(str(order_id)),
            order_side=self._map_order_side(venue_order.get("side")),
            order_type=self._map_order_type_from_venue(venue_order.get("type")),
            time_in_force=self._map_tif(venue_order.get("instruction")),
            order_status=venue_status,
            quantity=qty,
            filled_qty=filled_qty,
            report_id=UUID4(),
            ts_accepted=ts_init,
            ts_last=ts_last,
            ts_init=ts_init,
            client_order_id=report_client_order_id,
            price=price,
            trigger_price=trigger_price,
            trigger_type=trigger_type,
            avg_px=avg_px,
            reduce_only="REDUCE_ONLY" in [str(flag).upper() for flag in venue_order.get("flags", [])],
            cancel_reason=venue_order.get("cancel_reason"),
        )

    async def _fetch_open_orders(self, market: str | None) -> list[dict[str, Any]]:
        client = self._require_client()
        if not hasattr(client, "get_open_orders"):
            return []
        payload = await self._loop.run_in_executor(None, lambda: client.get_open_orders(market))
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    async def _fetch_orders_history(
        self,
        market: str | None,
        client_id: str | None,
        start_at_ms: int | None,
        end_at_ms: int | None,
        page_size: int,
    ) -> list[dict[str, Any]]:
        client = self._require_client()
        if not hasattr(client, "get_orders_history"):
            return []
        payload = await self._loop.run_in_executor(
            None,
            lambda: client.get_orders_history(market, client_id, start_at_ms, end_at_ms, page_size),
        )
        data = json.loads(payload) if isinstance(payload, str) else payload
        results = data.get("results", []) if isinstance(data, dict) else []
        return [item for item in results if isinstance(item, dict)]

    async def _collect_order_status_reports(
        self,
        instrument_id: Any | None,
        open_only: bool,
        client_order_id: str | None = None,
        venue_order_id: str | None = None,
        start_at_ms: int | None = None,
        end_at_ms: int | None = None,
    ) -> list[OrderStatusReport]:
        market = instrument_id.symbol.value if instrument_id is not None else None
        client = self._require_client()

        orders: list[dict[str, Any]] = []
        if client_order_id and hasattr(client, "get_order_by_client_id"):
            try:
                payload = await self._loop.run_in_executor(None, lambda: client.get_order_by_client_id(client_order_id))
                order = json.loads(payload) if isinstance(payload, str) else payload
                if isinstance(order, dict):
                    orders.append(order)
            except Exception:
                pass

        if venue_order_id and hasattr(client, "get_order_by_id"):
            try:
                payload = await self._loop.run_in_executor(None, lambda: client.get_order_by_id(venue_order_id))
                order = json.loads(payload) if isinstance(payload, str) else payload
                if isinstance(order, dict):
                    orders.append(order)
            except Exception:
                pass

        if not orders:
            orders.extend(await self._fetch_open_orders(market))
            if not open_only:
                orders.extend(
                    await self._fetch_orders_history(
                        market,
                        client_order_id,
                        start_at_ms,
                        end_at_ms,
                        self._reconciliation_page_size,
                    ),
                )

        dedup: dict[str, dict[str, Any]] = {}
        for item in orders:
            key = str(item.get("id") or item.get("client_id") or "")
            if key:
                dedup[key] = item

        reports: list[OrderStatusReport] = []
        for venue_order in dedup.values():
            report = self._build_order_status_report_from_venue(venue_order)
            if report is None:
                continue
            if instrument_id is not None and report.instrument_id != instrument_id:
                continue
            reports.append(report)

        return reports

    def _collect_position_status_reports(self, instrument_id: Any | None) -> list[PositionStatusReport]:
        positions = self._cache.positions(venue=self.venue, instrument_id=instrument_id)
        reports: list[PositionStatusReport] = []

        for position in positions:
            reports.append(
                PositionStatusReport(
                    account_id=self.account_id,
                    instrument_id=position.instrument_id,
                    position_side=position.side,
                    quantity=position.quantity,
                    report_id=UUID4(),
                    ts_last=position.ts_last,
                    ts_init=position.ts_init,
                    venue_position_id=position.id,
                    avg_px_open=position.avg_px_open,
                ),
            )

        return reports

    async def _submit_order_list(self, command: SubmitOrderList) -> None:
        """
        Submit a list of orders.
        """
        self._log.info(
            f"Submitting order list {command.order_list.id} with {len(command.order_list.orders)} orders",
            LogColor.BLUE,
        )

        for order in command.order_list.orders:
            await self._submit_single_order(
                strategy_id=command.strategy_id,
                instrument_id=order.instrument_id,
                order=order,
            )

    async def generate_order_status_report(self, command) -> OrderStatusReport | None:
        """
        Generate an order status report for a given order.
        """
        reports = await self._collect_order_status_reports(
            instrument_id=command.instrument_id,
            open_only=False,
            client_order_id=str(command.client_order_id) if command.client_order_id is not None else None,
            venue_order_id=str(command.venue_order_id) if command.venue_order_id is not None else None,
        )
        return reports[0] if reports else None

    async def generate_order_status_reports(self, command) -> list[OrderStatusReport]:
        """
        Generate order status reports.
        """
        return await self._collect_order_status_reports(
            instrument_id=command.instrument_id,
            open_only=getattr(command, "open_only", False),
            start_at_ms=self._ms_from_datetime(getattr(command, "start", None)),
            end_at_ms=self._ms_from_datetime(getattr(command, "end", None)),
        )

    async def generate_fill_reports(self, command) -> list[FillReport]:
        """
        Generate fill reports.
        """
        client = self._require_client()
        if not hasattr(client, "get_fills"):
            return []

        instrument_id = getattr(command, "instrument_id", None)
        market = instrument_id.symbol.value if instrument_id is not None else None
        start_at_ms = self._ms_from_datetime(getattr(command, "start", None))
        end_at_ms = self._ms_from_datetime(getattr(command, "end", None))

        payload = await self._loop.run_in_executor(
            None,
            lambda: client.get_fills(market, start_at_ms, end_at_ms, self._reconciliation_page_size),
        )
        data = json.loads(payload) if isinstance(payload, str) else payload
        venue_fills = data.get("results", []) if isinstance(data, dict) else []

        reports: list[FillReport] = []
        for fill in venue_fills:
            if not isinstance(fill, dict):
                continue
            market_name = fill.get("market")
            fill_instrument_id = self._instrument_id_from_market(market_name)
            if fill_instrument_id is None:
                continue
            if instrument_id is not None and fill_instrument_id != instrument_id:
                continue
            if command.venue_order_id is not None and str(fill.get("order_id")) != str(command.venue_order_id):
                continue

            fill_id = fill.get("id")
            order_id = fill.get("order_id")
            side = str(fill.get("side", "BUY")).upper()
            size = fill.get("size")
            price = fill.get("price")
            if not fill_id or not order_id or size in (None, "") or price in (None, ""):
                continue

            fee_value = self._parse_decimal(fill.get("fee"))
            fee_ccy = str(fill.get("fee_currency") or "USDC")
            commission = Money(fee_value, Currency.from_str(fee_ccy))

            cached_order = None
            if fill.get("client_id"):
                try:
                    cached_order = self._cache.order(ClientOrderId(str(fill.get("client_id"))))
                except Exception:
                    cached_order = None
            report_client_order_id = cached_order.client_order_id if cached_order is not None else None
            if report_client_order_id is not None:
                try:
                    report_client_order_id = ClientOrderId(str(report_client_order_id))
                except Exception:
                    report_client_order_id = None
            if report_client_order_id is None and fill.get("client_id"):
                try:
                    report_client_order_id = ClientOrderId(str(fill.get("client_id")))
                except Exception:
                    report_client_order_id = None

            report = FillReport(
                account_id=self.account_id,
                instrument_id=fill_instrument_id,
                venue_order_id=VenueOrderId(str(order_id)),
                trade_id=TradeId(str(fill_id)),
                order_side=self._map_order_side(side),
                last_qty=Quantity.from_str(str(size)),
                last_px=Price.from_str(str(price)),
                commission=commission,
                liquidity_side=self._map_liquidity(fill.get("liquidity")),
                report_id=UUID4(),
                ts_event=self._ns_from_ms(fill.get("created_at")) or self._clock.timestamp_ns(),
                ts_init=self._clock.timestamp_ns(),
                client_order_id=report_client_order_id,
                venue_position_id=None,
            )
            reports.append(report)

        return reports

    async def generate_position_status_reports(self, command) -> list[PositionStatusReport]:
        """
        Generate position status reports.
        """
        return self._collect_position_status_reports(instrument_id=command.instrument_id)

    async def generate_mass_status(
        self, lookback_mins: int | None = None
    ) -> ExecutionMassStatus | None:
        """
        Generate a mass execution status report.
        """
        effective_lookback_mins = lookback_mins if lookback_mins is not None else self._reconciliation_lookback_mins
        end_at_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_at_ms = end_at_ms - (max(int(effective_lookback_mins), 1) * 60 * 1000)

        mass = ExecutionMassStatus(
            client_id=self.id,
            account_id=self.account_id,
            venue=self.venue,
            report_id=UUID4(),
            ts_init=self._clock.timestamp_ns(),
        )
        mass.add_order_reports(
            await self._collect_order_status_reports(
                instrument_id=None,
                open_only=False,
                start_at_ms=start_at_ms,
                end_at_ms=end_at_ms,
            ),
        )
        fills = await self.generate_fill_reports(
            command=type(
                "_Cmd",
                (),
                {
                    "instrument_id": None,
                    "venue_order_id": None,
                    "start": start_at_ms,
                    "end": end_at_ms,
                },
            )(),
        )
        mass.add_fill_reports(fills)
        mass.add_position_reports(self._collect_position_status_reports(instrument_id=None))
        return mass
