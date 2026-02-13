import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogColor
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import NautilusConfig
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import BatchCancelOrders
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import CancelOrder
from nautilus_trader.execution.messages import ModifyOrder
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.execution.messages import SubmitOrderList
from nautilus_trader.execution.reports import ExecutionMassStatus
from nautilus_trader.execution.reports import FillReport
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.enums import TriggerType
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.objects import MarginBalance
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity

from .constants import REST_URL_MAINNET
from .constants import REST_URL_TESTNET
from .constants import WS_URL_PRIVATE


class LighterExecutionClient(LiveExecutionClient):
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
        self._base_url = getattr(config, "base_url_http", None) or (
            REST_URL_TESTNET if is_testnet else REST_URL_MAINNET
        )
        self._ws_url = getattr(config, "base_url_ws", None) or WS_URL_PRIVATE
        configured_lookback = (
            getattr(config, "reconciliation_lookback_mins", None) if config is not None else None
        )
        self._reconciliation_lookback_mins = (
            int(configured_lookback) if configured_lookback is not None else 120
        )
        configured_page_size = (
            getattr(config, "reconciliation_page_size", 100) if config is not None else 100
        )
        self._reconciliation_page_size = max(1, min(int(configured_page_size), 200))
        self._set_account_id(AccountId(f"{venue.value}-001"))

    def _require_client(self) -> Any:
        if self._client is None:
            raise RuntimeError("Lighter execution client backend is not configured")
        return self._client

    async def _call_client(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        client = self._require_client()
        method = getattr(client, method_name)
        result = method(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

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
        if t in {"STOP_MARKET", "STOP_LOSS_MARKET"}:
            return OrderType.STOP_MARKET
        if t in {"STOP_LIMIT", "STOP_LOSS_LIMIT"}:
            return OrderType.STOP_LIMIT
        if t in {"TAKE_PROFIT_LIMIT"}:
            return OrderType.LIMIT_IF_TOUCHED
        if t in {"TAKE_PROFIT_MARKET"}:
            return OrderType.MARKET_IF_TOUCHED
        return OrderType.LIMIT

    @classmethod
    def _map_order_status_from_venue(cls, venue_order: dict[str, Any]) -> OrderStatus:
        status = str(venue_order.get("status", "OPEN")).upper()
        size = cls._parse_decimal(venue_order.get("initial_base_amount") or venue_order.get("size"))
        remaining = cls._parse_decimal(
            venue_order.get("remaining_base_amount") or venue_order.get("remaining_size"), size
        )
        filled = cls._parse_decimal(
            venue_order.get("filled_base_amount"),
            size - remaining if size >= remaining else Decimal("0"),
        )

        if "REJECT" in status:
            return OrderStatus.REJECTED
        if "CANCEL" in status:
            return OrderStatus.CANCELED
        if "EXPIRE" in status:
            return OrderStatus.EXPIRED
        if status in {"OPEN", "NEW", "UNTRIGGERED", "PENDING", "IN_PROGRESS"}:
            if filled > Decimal("0"):
                return OrderStatus.PARTIALLY_FILLED
            return OrderStatus.ACCEPTED
        if "FILL" in status and filled > Decimal("0"):
            return OrderStatus.FILLED
        if filled > Decimal("0"):
            return OrderStatus.PARTIALLY_FILLED
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
        upper = market.upper()
        if upper.endswith("-USD-PERP"):
            symbol = upper
        else:
            symbol = f"{upper}-USD-PERP"
        try:
            return InstrumentId.from_str(f"{symbol}.{self.venue.value}")
        except Exception:
            return None

    async def _connect(self) -> None:
        self._log.info("Connecting to Lighter execution...", LogColor.BLUE)
        probe = await self._call_client("check_connection")
        if not probe.get("ok", False):
            raise RuntimeError(str(probe.get("error") or "Unknown Lighter connection error"))

        await self._instrument_provider.load_all_async()
        for instrument in self._instrument_provider.get_all().values():
            self._cache.add_instrument(instrument)
        for currency in self._instrument_provider.currencies().values():
            self._cache.add_currency(currency)
        await self._update_account_state()
        await self._await_account_registered()

    async def _update_account_state(self) -> None:
        currency = Currency.from_str("USD")
        total_balance = Decimal("0")
        free_balance = Decimal("0")
        locked_balance = Decimal("0")
        initial_margin = Decimal("0")

        try:
            snapshot = await self._call_client("get_account_state")
            collateral = self._parse_decimal(snapshot.get("collateral"))
            available = self._parse_decimal(snapshot.get("available_balance"))
            total_asset = self._parse_decimal(snapshot.get("total_asset_value"), collateral)

            total_balance = total_asset if total_asset > Decimal("0") else collateral
            free_balance = available
            locked_balance = max(total_balance - free_balance, Decimal("0"))

            positions = snapshot.get("positions") or []
            for pos in positions:
                initial_margin += self._parse_decimal(pos.get("allocated_margin"))
        except Exception as e:
            self._log.warning(
                f"Failed to fetch live Lighter account snapshot, falling back to zero balances: {e}",
                LogColor.YELLOW,
            )

        total_money = Money(total_balance, currency)
        free_money = Money(free_balance, currency)
        locked_money = Money(locked_balance, currency)
        initial_margin_money = Money(initial_margin, currency)
        maintenance_margin_money = Money(Decimal("0"), currency)

        self.generate_account_state(
            balances=[
                AccountBalance(
                    total=total_money,
                    locked=locked_money,
                    free=free_money,
                ),
            ],
            margins=[
                MarginBalance(
                    initial=initial_margin_money,
                    maintenance=maintenance_margin_money,
                    instrument_id=None,
                ),
            ],
            reported=True,
            ts_event=self._clock.timestamp_ns(),
        )

    async def _disconnect(self) -> None:
        self._log.info("Disconnecting from Lighter execution...", LogColor.BLUE)
        client = self._client
        if client is not None and hasattr(client, "close"):
            typed_client: Any = client
            close_result = typed_client.close()
            if asyncio.iscoroutine(close_result):
                await close_result

    @classmethod
    def _map_order_type(cls, order: Any) -> str:
        order_type = order.type_string().upper()
        if order_type in {"LIMIT", "MARKET"}:
            return order_type
        if order_type == "LIMIT_IF_TOUCHED":
            return "TAKE_PROFIT_LIMIT"
        if order_type == "MARKET_IF_TOUCHED":
            return "TAKE_PROFIT_MARKET"
        if order_type == "STOP_LIMIT":
            return "STOP_LOSS_LIMIT"
        if order_type == "STOP_MARKET":
            return "STOP_LOSS_MARKET"
        return "LIMIT"

    async def _submit_order(self, command: SubmitOrder) -> None:
        self._log.info(
            f"Submitting {command.order.type_string()} order for {command.instrument_id}",
            LogColor.BLUE,
        )
        await self._submit_single_order(
            strategy_id=command.strategy_id,
            instrument_id=command.instrument_id,
            order=command.order,
        )

    async def _submit_single_order(self, strategy_id: Any, instrument_id: Any, order: Any) -> None:
        order_type = self._map_order_type(order)
        side = order.side_string().upper()
        size = str(order.quantity)
        min_price_types = {
            "MARKET",
            "STOP_MARKET",
            "STOP_LOSS_MARKET",
            "TAKE_PROFIT_MARKET",
            "TAKE_PROFIT",
        }
        price = (
            str(order.price) if order.has_price else ("1" if order_type in min_price_types else "0")
        )
        trigger_price = str(order.trigger_price) if order.has_trigger_price else None
        instruction = order.tif_string().upper() if hasattr(order, "tif_string") else "GTC"
        if order_type == "MARKET":
            instruction = "IOC"
        client_order_id = str(order.client_order_id)

        self.generate_order_submitted(
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            client_order_id=order.client_order_id,
            ts_event=self._clock.timestamp_ns(),
        )

        try:
            result = await self._call_client(
                "submit_order",
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
            )

            venue_id = result.get("action_id") or result.get("id")
            if venue_id is None:
                raise RuntimeError("Venue response missing order identifier")

            self.generate_order_accepted(
                strategy_id=strategy_id,
                instrument_id=instrument_id,
                client_order_id=order.client_order_id,
                venue_order_id=VenueOrderId(str(venue_id)),
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
        self._log.info(f"Canceling order {command.client_order_id}", LogColor.BLUE)

        def _is_not_found_error(exc: Exception) -> bool:
            message = str(exc).upper()
            return (
                "ORDER_ID_NOT_FOUND" in message
                or "CLIENT_ORDER_ID_NOT_FOUND" in message
                or "NOT FOUND" in message
                or "UNKNOWN ORDER" in message
                or "404" in message
            )

        try:
            try:
                await self._call_client(
                    "cancel_order_by_client_id",
                    str(command.client_order_id),
                    command.instrument_id.symbol.value
                    if command.instrument_id is not None
                    else None,
                )
            except Exception:
                venue_order_id = (
                    str(command.venue_order_id) if command.venue_order_id is not None else None
                )
                if venue_order_id is None:
                    raise
                await self._call_client("cancel_order", venue_order_id)

            self.generate_order_canceled(
                strategy_id=command.strategy_id,
                instrument_id=command.instrument_id,
                client_order_id=command.client_order_id,
                venue_order_id=command.venue_order_id,
                ts_event=self._clock.timestamp_ns(),
            )
        except Exception as e:
            if _is_not_found_error(e):
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
        instrument_id = getattr(command, "instrument_id", None)
        market = instrument_id.symbol.value if instrument_id is not None else None
        try:
            await self._call_client("cancel_all_orders", market)
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
                reason="Modify order is not available in current Lighter client build",
                ts_event=self._clock.timestamp_ns(),
            )
            return

        def _is_order_not_open_error(exc: Exception) -> bool:
            text = str(exc).upper()
            return "ORDER_IS_NOT_OPEN" in text or "CANNOT BE MODIFIED" in text

        try:
            existing = None
            if command.venue_order_id is not None:
                existing = await self._call_client("get_order_by_id", str(command.venue_order_id))
            if existing is None:
                existing = await self._call_client(
                    "get_order_by_client_id", str(command.client_order_id)
                )
            if not isinstance(existing, dict):
                raise RuntimeError("Unexpected modify lookup payload")

            order_id = str(
                existing.get("order_index")
                or existing.get("order_id")
                or command.venue_order_id
                or ""
            )
            market = str(existing.get("market") or command.instrument_id.symbol.value)
            side = "SELL" if existing.get("is_ask") else "BUY"
            order_type = str(existing.get("type") or "LIMIT")

            size = (
                str(command.quantity)
                if command.quantity is not None
                else str(existing.get("initial_base_amount") or existing.get("size") or "0")
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

            async def _call_modify() -> Any:
                return await self._call_client(
                    "modify_order",
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
                modified = await _call_modify()
            except Exception as first_error:
                if not _is_order_not_open_error(first_error):
                    raise
                latest = await self._call_client("get_order_by_id", order_id)
                latest_status = (
                    str(latest.get("status", "")).upper() if isinstance(latest, dict) else ""
                )
                if latest_status in {"NEW", "UNTRIGGERED", "OPEN"}:
                    await asyncio.sleep(0.25)
                    modified = await _call_modify()
                else:
                    raise

            if not isinstance(modified, dict):
                raise RuntimeError("Unexpected modify response payload")

            updated_venue_order_id = VenueOrderId(
                str(modified.get("order_index") or modified.get("order_id") or order_id)
            )
            venue_order_id_modified = command.venue_order_id is not None and str(
                updated_venue_order_id
            ) != str(command.venue_order_id)

            updated_qty = (
                command.quantity if command.quantity is not None else Quantity.from_str(size)
            )
            updated_price = command.price if command.price is not None else Price.from_str(price)
            updated_trigger = (
                command.trigger_price
                if command.trigger_price is not None
                else (
                    Price.from_str(str(trigger_price)) if trigger_price not in (None, "") else None
                )
            )

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
        for cancel_command in command.cancels:
            await self._cancel_order(cancel_command)

    async def _submit_order_list(self, command: SubmitOrderList) -> None:
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

    def _build_order_status_report_from_venue(
        self, venue_order: dict[str, Any]
    ) -> OrderStatusReport | None:
        order_id = venue_order.get("order_index") or venue_order.get("order_id")
        market_id = venue_order.get("market_index") or venue_order.get("market_id")
        instrument_id = self._instrument_id_from_market(
            str(market_id) if market_id is not None else None
        )
        if not order_id or instrument_id is None:
            return None

        size = self._parse_decimal(
            venue_order.get("initial_base_amount") or venue_order.get("size")
        )
        remaining = self._parse_decimal(
            venue_order.get("remaining_base_amount") or venue_order.get("remaining_size"), size
        )
        filled = size - remaining if size >= remaining else Decimal("0")
        venue_status = self._map_order_status_from_venue(venue_order)

        client_order_id = venue_order.get("client_order_index") or venue_order.get(
            "client_order_id"
        )
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
        trigger_type = (
            self._map_trigger_type(venue_order.get("trigger_type"))
            if trigger_price is not None
            else TriggerType.NO_TRIGGER
        )
        avg_px = self._parse_decimal(avg_fill_val) if avg_fill_val not in (None, "") else None

        ts_init = (
            self._ns_from_ms(venue_order.get("created_at") or venue_order.get("timestamp"))
            or self._clock.timestamp_ns()
        )
        ts_last = (
            self._ns_from_ms(venue_order.get("updated_at") or venue_order.get("timestamp"))
            or ts_init
        )

        report_client_order_id = cached_order.client_order_id if cached_order is not None else None
        if report_client_order_id is None and client_order_id is not None:
            try:
                report_client_order_id = ClientOrderId(str(client_order_id))
            except Exception:
                report_client_order_id = None

        return OrderStatusReport(
            account_id=self.account_id,
            instrument_id=instrument_id,
            venue_order_id=VenueOrderId(str(order_id)),
            order_side=self._map_order_side("SELL" if venue_order.get("is_ask") else "BUY"),
            order_type=self._map_order_type_from_venue(venue_order.get("type")),
            time_in_force=self._map_tif(venue_order.get("time_in_force")),
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
            reduce_only=bool(venue_order.get("reduce_only", False)),
            cancel_reason=venue_order.get("status")
            if "cancel" in str(venue_order.get("status", "")).lower()
            else None,
        )

    async def _fetch_open_orders(self, market: str | None) -> list[dict[str, Any]]:
        payload = await self._call_client("get_open_orders", market)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    async def _fetch_orders_history(
        self,
        market: str | None,
        client_id: str | None,
        start_at_ms: int | None,
        end_at_ms: int | None,
        page_size: int,
    ) -> list[dict[str, Any]]:
        payload = await self._call_client(
            "get_orders_history",
            market,
            client_id,
            start_at_ms,
            end_at_ms,
            page_size,
        )
        results = payload.get("results", []) if isinstance(payload, dict) else []
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

        orders: list[dict[str, Any]] = []
        if client_order_id:
            try:
                order = await self._call_client("get_order_by_client_id", client_order_id)
                if isinstance(order, dict):
                    orders.append(order)
            except Exception:
                pass

        if venue_order_id:
            try:
                order = await self._call_client("get_order_by_id", venue_order_id)
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
            key = str(item.get("order_index") or item.get("client_order_index") or "")
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

    def _collect_position_status_reports(
        self, instrument_id: Any | None
    ) -> list[PositionStatusReport]:
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

    async def generate_order_status_report(self, command) -> OrderStatusReport | None:
        reports = await self._collect_order_status_reports(
            instrument_id=command.instrument_id,
            open_only=False,
            client_order_id=str(command.client_order_id)
            if command.client_order_id is not None
            else None,
            venue_order_id=str(command.venue_order_id)
            if command.venue_order_id is not None
            else None,
        )
        return reports[0] if reports else None

    async def generate_order_status_reports(self, command) -> list[OrderStatusReport]:
        return await self._collect_order_status_reports(
            instrument_id=command.instrument_id,
            open_only=getattr(command, "open_only", False),
            start_at_ms=self._ms_from_datetime(getattr(command, "start", None)),
            end_at_ms=self._ms_from_datetime(getattr(command, "end", None)),
        )

    async def generate_fill_reports(self, command) -> list[FillReport]:
        instrument_id = getattr(command, "instrument_id", None)
        market = instrument_id.symbol.value if instrument_id is not None else None
        start_at_ms = self._ms_from_datetime(getattr(command, "start", None))
        end_at_ms = self._ms_from_datetime(getattr(command, "end", None))

        payload = await self._call_client(
            "get_fills",
            market,
            start_at_ms,
            end_at_ms,
            self._reconciliation_page_size,
        )
        rows = payload.get("results", []) if isinstance(payload, dict) else []

        reports: list[FillReport] = []
        for row in rows:
            try:
                market_id = row.get("market_id") or row.get("market_index")
                fill_instrument = self._instrument_id_from_market(
                    str(market_id) if market_id is not None else market
                )
                if fill_instrument is None:
                    continue

                quantity = Quantity.from_str(str(row.get("base_amount") or row.get("size") or "0"))
                px = Price.from_str(str(row.get("price") or "0"))
                ts_event = (
                    self._ns_from_ms(int(row.get("timestamp", 0)) * 1000)
                    or self._clock.timestamp_ns()
                )

                is_sell = bool(row.get("is_ask"))
                is_maker_ask = bool(row.get("is_maker_ask"))
                is_maker = (is_sell and is_maker_ask) or ((not is_sell) and (not is_maker_ask))
                liquidity = LiquiditySide.MAKER if is_maker else LiquiditySide.TAKER

                fee_raw = row.get("maker_fee") if is_maker else row.get("taker_fee")
                if fee_raw in (None, ""):
                    fee_raw = row.get("fee")
                commission = (
                    Money(self._parse_decimal(fee_raw), Currency.from_str("USD"))
                    if fee_raw not in (None, "")
                    else None
                )

                client_id_value = row.get("client_order_index")
                if client_id_value in (None, ""):
                    client_id_value = (
                        row.get("ask_client_id") if is_sell else row.get("bid_client_id")
                    )

                reports.append(
                    FillReport(
                        account_id=self.account_id,
                        instrument_id=fill_instrument,
                        venue_order_id=VenueOrderId(
                            str(row.get("order_index") or row.get("order_id") or "0")
                        ),
                        venue_position_id=None,
                        trade_id=TradeId(str(row.get("trade_id") or row.get("id") or UUID4())),
                        order_side=self._map_order_side("SELL" if is_sell else "BUY"),
                        last_qty=quantity,
                        last_px=px,
                        commission=commission,
                        liquidity_side=liquidity,
                        report_id=UUID4(),
                        ts_event=ts_event,
                        ts_init=ts_event,
                        client_order_id=ClientOrderId(str(client_id_value))
                        if client_id_value is not None
                        else None,
                    ),
                )
            except Exception:
                continue
        return reports

    async def generate_position_status_reports(self, command) -> list[PositionStatusReport]:
        instrument_id = getattr(command, "instrument_id", None)
        return self._collect_position_status_reports(instrument_id)

    async def generate_mass_status(
        self, lookback_mins: int | None = None
    ) -> ExecutionMassStatus | None:
        if not self.is_connected:
            self._log.warning(
                "Cannot generate mass status while execution client is disconnected",
            )
            return None

        from nautilus_trader.execution.messages import GenerateFillReports
        from nautilus_trader.execution.messages import GenerateOrderStatusReports
        from nautilus_trader.execution.messages import GeneratePositionStatusReports

        lookback = lookback_mins or self._reconciliation_lookback_mins
        start = datetime.now(tz=timezone.utc) - timedelta(minutes=lookback)

        self.reconciliation_active = True
        try:
            report_id = UUID4()
            ts_init = self._clock.timestamp_ns()
            command_id = UUID4()

            mass_status = ExecutionMassStatus(
                client_id=self.id,
                account_id=self.account_id,
                venue=self.venue,
                report_id=report_id,
                ts_init=ts_init,
            )

            order_reports, fill_reports, position_reports = await asyncio.gather(
                self.generate_order_status_reports(
                    GenerateOrderStatusReports(
                        instrument_id=None,
                        start=start,
                        end=None,
                        open_only=False,
                        command_id=command_id,
                        ts_init=ts_init,
                    ),
                ),
                self.generate_fill_reports(
                    GenerateFillReports(
                        instrument_id=None,
                        venue_order_id=None,
                        start=start,
                        end=None,
                        command_id=command_id,
                        ts_init=ts_init,
                    ),
                ),
                self.generate_position_status_reports(
                    GeneratePositionStatusReports(
                        instrument_id=None,
                        start=start,
                        end=None,
                        command_id=command_id,
                        ts_init=ts_init,
                    ),
                ),
            )

            mass_status.add_order_reports(order_reports)
            mass_status.add_fill_reports(fill_reports)
            mass_status.add_position_reports(position_reports)
            return mass_status
        finally:
            self.reconciliation_active = False
