import time
import hashlib
import inspect
import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Awaitable, cast


@dataclass
class _MarketMeta:
    symbol: str
    market_id: int
    size_decimals: int
    price_decimals: int
    min_base_amount: Decimal


class LighterSdkBackend:
    _MAX_CLIENT_ORDER_INDEX = 281_474_976_710_655

    def __init__(
        self,
        base_url: str,
        account_index: int,
        api_key_index: int,
        api_key_private_key: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._account_index = account_index
        self._api_key_index = api_key_index
        self._api_key_private_key = api_key_private_key

        self._lighter: Any | None = None
        self._signer: Any | None = None
        self._api_client: Any | None = None
        self._order_api: Any | None = None
        self._account_api: Any | None = None
        self._market_by_symbol: dict[str, _MarketMeta] = {}
        self._market_by_id: dict[int, _MarketMeta] = {}

    async def _close_handle(self, handle: Any | None) -> None:
        if handle is None:
            return
        close_fn = getattr(handle, "close", None)
        if callable(close_fn):
            result = close_fn()
            if inspect.isawaitable(result):
                await cast(Awaitable[Any], result)

    async def _close_nested_handles(self, handle: Any | None) -> None:
        if handle is None:
            return
        for attr in ("api_client", "_api_client", "session", "_session"):
            nested = getattr(handle, attr, None)
            await self._close_handle(nested)

    async def _close_api_client(self, api_client: Any | None) -> None:
        if api_client is None:
            return
        await self._close_handle(api_client)
        rest_client = getattr(api_client, "rest_client", None)
        await self._close_handle(rest_client)
        if rest_client is not None:
            pool_manager = getattr(rest_client, "pool_manager", None)
            await self._close_handle(pool_manager)

    async def _ensure_sdk(self) -> None:
        if self._lighter is not None:
            return
        try:
            import lighter as lighter_sdk  # type: ignore
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Missing Python package `lighter`. Install it in this environment to run "
                "Lighter live clients/canaries."
            ) from exc

        self._lighter = lighter_sdk

    async def _ensure_clients(self) -> None:
        await self._ensure_sdk()
        assert self._lighter is not None

        if self._api_client is None:
            self._api_client = self._lighter.ApiClient(
                configuration=self._lighter.Configuration(host=self._base_url),
            )
            self._order_api = self._lighter.OrderApi(self._api_client)
            self._account_api = self._lighter.AccountApi(self._api_client)

        if self._signer is None:
            self._signer = self._lighter.SignerClient(
                url=self._base_url,
                api_private_keys={self._api_key_index: self._api_key_private_key},
                account_index=self._account_index,
            )

    async def _with_rate_limit_retries(self, call, attempts: int = 5) -> Any:
        for attempt in range(attempts):
            try:
                return await call()
            except Exception as exc:
                message = str(exc).upper()
                is_rate_limit = "TOO MANY REQUESTS" in message or "429" in message
                if (not is_rate_limit) or attempt == attempts - 1:
                    raise
                await asyncio.sleep(0.25 * (2**attempt))

    async def close(self) -> None:
        api_clients: list[Any] = []
        for candidate in (
            self._api_client,
            getattr(self._order_api, "api_client", None),
            getattr(self._account_api, "api_client", None),
            getattr(self._signer, "api_client", None),
            getattr(getattr(self._signer, "order_api", None), "api_client", None),
            getattr(getattr(self._signer, "tx_api", None), "api_client", None),
        ):
            if candidate is not None and candidate not in api_clients:
                api_clients.append(candidate)

        for api_client in api_clients:
            await self._close_api_client(api_client)

        await self._close_handle(self._order_api)
        await self._close_handle(self._account_api)
        await self._close_handle(self._signer)
        await self._close_handle(self._api_client)
        self._api_client = None
        self._order_api = None
        self._account_api = None
        self._signer = None

    async def _auth_token(self) -> str:
        await self._ensure_clients()
        assert self._signer is not None
        token, err = self._signer.create_auth_token_with_expiry(
            deadline=3600,
            api_key_index=self._api_key_index,
        )
        if err:
            raise RuntimeError(f"Failed to build Lighter auth token: {err}")
        return token

    @staticmethod
    def _norm_symbol(symbol: str) -> str:
        s = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
        if s.endswith("PERP"):
            s = s[:-4]
        if s.endswith("USD"):
            s = s[:-3]
        if s.endswith("USDC"):
            s = s[:-4]
        return s

    @classmethod
    def _client_order_index(cls, client_id: str) -> int:
        raw = str(client_id).strip()
        try:
            parsed = int(raw)
            if parsed <= 0:
                return 1
            return min(parsed, cls._MAX_CLIENT_ORDER_INDEX)
        except Exception:
            digest = hashlib.sha256(raw.encode("utf-8")).digest()
            return (
                int.from_bytes(digest[:8], byteorder="big", signed=False)
                % cls._MAX_CLIENT_ORDER_INDEX
            ) + 1

    @classmethod
    def _matches_client_id(cls, order: dict[str, Any], client_id: str) -> bool:
        candidate = str(client_id)
        mapped = str(cls._client_order_index(client_id))
        return str(order.get("client_order_index")) in {candidate, mapped} or str(
            order.get("client_order_id")
        ) in {candidate, mapped}

    async def _refresh_markets(self) -> None:
        await self._ensure_clients()
        assert self._order_api is not None
        order_api = cast(Any, self._order_api)
        payload = await self._with_rate_limit_retries(lambda: order_api.order_books())
        raw = payload.model_dump().get("order_books", [])

        by_symbol: dict[str, _MarketMeta] = {}
        by_id: dict[int, _MarketMeta] = {}

        for row in raw:
            try:
                symbol = str(row.get("symbol", ""))
                market_id = int(row["market_id"])
                size_dec = int(row.get("supported_size_decimals", 5))
                price_dec = int(row.get("supported_price_decimals", 1))
                min_base_amount = Decimal(str(row.get("min_base_amount", "0.00001")))
            except Exception:
                continue

            meta = _MarketMeta(
                symbol=symbol,
                market_id=market_id,
                size_decimals=size_dec,
                price_decimals=price_dec,
                min_base_amount=min_base_amount,
            )
            by_symbol[self._norm_symbol(symbol)] = meta
            by_id[market_id] = meta

        self._market_by_symbol = by_symbol
        self._market_by_id = by_id

    async def check_connection(self) -> dict[str, Any]:
        await self._ensure_clients()
        assert self._signer is not None
        check_error = self._signer.check_client()
        await self._refresh_markets()
        return {
            "ok": check_error is None,
            "error": check_error,
            "timestamp_ms": int(time.time() * 1000),
            "markets": len(self._market_by_id),
        }

    async def get_info(self) -> dict[str, Any]:
        await self._refresh_markets()
        return {
            "results": [
                {
                    "market_id": m.market_id,
                    "symbol": m.symbol,
                    "size_decimals": m.size_decimals,
                    "price_decimals": m.price_decimals,
                    "min_base_amount": str(m.min_base_amount),
                }
                for m in self._market_by_id.values()
            ],
        }

    async def get_account_state(self) -> dict[str, Any]:
        await self._ensure_clients()
        assert self._account_api is not None
        account_api = cast(Any, self._account_api)

        account_payload = await account_api.account(by="index", value=str(self._account_index))
        account_rows = account_payload.model_dump().get("accounts", [])
        if not account_rows:
            raise RuntimeError(f"No account row returned for index {self._account_index}")

        account_row = account_rows[0]
        metadata_name = None
        metadata_description = None
        limits_payload = None
        try:
            auth = await self._auth_token()
            metadata_payload = await account_api.account_metadata(
                by="index",
                value=str(self._account_index),
                auth=auth,
            )
            metadata_rows = metadata_payload.model_dump().get("account_metadatas", [])
            if metadata_rows:
                metadata_name = metadata_rows[0].get("name")
                metadata_description = metadata_rows[0].get("description")

            limits = await account_api.account_limits(account_index=self._account_index, auth=auth)
            limits_payload = limits.model_dump()
        except Exception:
            limits_payload = None

        return {
            "account_index": account_row.get("account_index") or account_row.get("index"),
            "available_balance": account_row.get("available_balance"),
            "collateral": account_row.get("collateral"),
            "total_asset_value": account_row.get("total_asset_value"),
            "cross_asset_value": account_row.get("cross_asset_value"),
            "pending_order_count": account_row.get("pending_order_count"),
            "positions": account_row.get("positions") or [],
            "assets": account_row.get("assets") or [],
            "name": metadata_name,
            "description": metadata_description,
            "limits": limits_payload,
            "raw": account_row,
        }

    async def get_orderbook(self, market: str, limit: int = 20) -> dict[str, Any]:
        await self._ensure_clients()
        if not self._market_by_id:
            await self._refresh_markets()
        assert self._order_api is not None
        order_api = cast(Any, self._order_api)

        meta = self._resolve_market(market)
        payload = await self._with_rate_limit_retries(
            lambda: order_api.order_book_orders(
                market_id=meta.market_id,
                limit=max(1, int(limit)),
            )
        )
        data = payload.model_dump()
        return {
            "market": meta.symbol,
            "market_id": meta.market_id,
            "bids": data.get("bids", []),
            "asks": data.get("asks", []),
        }

    def _resolve_market(self, market: str | None) -> _MarketMeta:
        if not self._market_by_id:
            raise RuntimeError("Lighter markets not loaded")
        if market is None:
            raise RuntimeError("Market must be provided")

        if market.isdigit():
            market_id = int(market)
            if market_id in self._market_by_id:
                return self._market_by_id[market_id]

        norm = self._norm_symbol(market)
        if norm in self._market_by_symbol:
            return self._market_by_symbol[norm]

        raise RuntimeError(f"Unable to resolve Lighter market '{market}'")

    def _order_ints(
        self,
        meta: _MarketMeta,
        size: str,
        price: str,
    ) -> tuple[int, int]:
        base_amount = int((Decimal(size) * (Decimal(10) ** meta.size_decimals)).to_integral_value())
        min_amount = int(
            (meta.min_base_amount * (Decimal(10) ** meta.size_decimals)).to_integral_value()
        )
        if base_amount < max(min_amount, 1):
            base_amount = max(min_amount, 1)
        price_int = int((Decimal(price) * (Decimal(10) ** meta.price_decimals)).to_integral_value())
        return base_amount, price_int

    async def submit_order(
        self,
        market: str,
        side: str,
        order_type: str,
        size: str,
        price: str,
        client_id: str,
        instruction: str,
        trigger_price: str | None,
        reduce_only: bool,
        _signature_timestamp_ms: int | None,
    ) -> dict[str, Any]:
        await self._ensure_clients()
        if not self._market_by_id:
            await self._refresh_markets()

        meta = self._resolve_market(market)
        assert self._signer is not None and self._lighter is not None

        base_amount, price_int = self._order_ints(meta, size=size, price=price)
        is_ask = side.upper() == "SELL"
        coi = self._client_order_index(client_id)

        order_type_upper = order_type.upper()
        if order_type_upper == "MARKET":
            venue_order_type = self._signer.ORDER_TYPE_MARKET
        else:
            venue_order_type = self._signer.ORDER_TYPE_LIMIT

        tif_upper = instruction.upper()
        if tif_upper == "IOC":
            tif = self._signer.ORDER_TIME_IN_FORCE_IMMEDIATE_OR_CANCEL
            expiry = 0
        elif tif_upper == "POST_ONLY":
            tif = self._signer.ORDER_TIME_IN_FORCE_POST_ONLY
            expiry = 0
        else:
            tif = self._signer.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME
            expiry = -1

        tx_info, tx_hash, err = await self._signer.create_order(
            market_index=meta.market_id,
            client_order_index=coi,
            base_amount=base_amount,
            price=price_int,
            is_ask=is_ask,
            order_type=venue_order_type,
            time_in_force=tif,
            reduce_only=reduce_only,
            trigger_price=int(
                (Decimal(trigger_price) * (Decimal(10) ** meta.price_decimals)).to_integral_value()
            )
            if trigger_price not in (None, "")
            else 0,
            order_expiry=expiry,
            api_key_index=self._api_key_index,
        )
        if err:
            raise RuntimeError(str(err))

        tx_hash_str = None
        if tx_hash is not None:
            if hasattr(tx_hash, "tx_hash"):
                tx_hash_str = str(tx_hash.tx_hash)
            else:
                tx_hash_str = str(tx_hash)

        return {
            "id": tx_hash_str,
            "action_id": tx_hash_str,
            "client_id": str(client_id),
            "market": meta.symbol,
            "market_id": meta.market_id,
            "side": "SELL" if is_ask else "BUY",
            "type": "MARKET" if order_type_upper == "MARKET" else "LIMIT",
            "instruction": tif_upper,
            "price": str(price),
            "size": str(size),
            "tx_info": tx_info.to_dict() if hasattr(tx_info, "to_dict") else None,
        }

    async def _fetch_order_lists(
        self, market_id: int | None = None
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        await self._ensure_clients()
        assert self._order_api is not None
        order_api = cast(Any, self._order_api)
        auth = await self._auth_token()

        active: list[dict[str, Any]] = []
        inactive: list[dict[str, Any]] = []

        if market_id is not None:
            active_payload = await self._with_rate_limit_retries(
                lambda: order_api.account_active_orders(
                    account_index=self._account_index,
                    market_id=market_id,
                    auth=auth,
                )
            )
            active = active_payload.model_dump().get("orders", [])

        inactive_payload = await self._with_rate_limit_retries(
            lambda: order_api.account_inactive_orders(
                account_index=self._account_index,
                market_id=market_id,
                limit=100,
                auth=auth,
            )
        )
        inactive = inactive_payload.model_dump().get("orders", [])
        return active, inactive

    async def get_open_orders(self, market: str | None = None) -> list[dict[str, Any]]:
        if not self._market_by_id:
            await self._refresh_markets()
        market_id = self._resolve_market(market).market_id if market is not None else None
        active, _ = await self._fetch_order_lists(market_id)
        return active

    async def get_order_by_client_id(self, client_id: str) -> dict[str, Any]:
        if not self._market_by_id:
            await self._refresh_markets()
        for market_id in self._market_by_id:
            active, inactive = await self._fetch_order_lists(market_id)
            for order in active + inactive:
                if self._matches_client_id(order, client_id):
                    return order
        raise RuntimeError(f"Order not found for client_id={client_id}")

    async def get_order_by_id(self, order_id: str) -> dict[str, Any]:
        if not self._market_by_id:
            await self._refresh_markets()
        for market_id in self._market_by_id:
            active, inactive = await self._fetch_order_lists(market_id)
            for order in active + inactive:
                if str(order.get("order_index")) == str(order_id) or str(
                    order.get("order_id")
                ) == str(order_id):
                    return order
        raise RuntimeError(f"Order not found for order_id={order_id}")

    async def get_orders_history(
        self,
        market: str | None,
        client_id: str | None,
        start_at_ms: int | None,
        end_at_ms: int | None,
        page_size: int | None,
    ) -> dict[str, Any]:
        if not self._market_by_id:
            await self._refresh_markets()
        market_id = self._resolve_market(market).market_id if market is not None else None
        _, inactive = await self._fetch_order_lists(market_id)

        results = inactive
        if client_id is not None:
            results = [o for o in results if self._matches_client_id(o, client_id)]

        if start_at_ms is not None:
            start_s = int(start_at_ms / 1000)
            results = [o for o in results if int(o.get("timestamp", 0)) >= start_s]
        if end_at_ms is not None:
            end_s = int(end_at_ms / 1000)
            results = [o for o in results if int(o.get("timestamp", 0)) <= end_s]

        limit = page_size or 100
        return {"results": results[:limit], "next": None, "prev": None}

    async def get_fills(
        self,
        market: str | None,
        start_at_ms: int | None,
        end_at_ms: int | None,
        page_size: int | None,
    ) -> dict[str, Any]:
        await self._ensure_clients()
        if not self._market_by_id:
            await self._refresh_markets()

        assert self._order_api is not None
        order_api = cast(Any, self._order_api)
        auth = await self._auth_token()
        market_id = self._resolve_market(market).market_id if market is not None else None
        limit = page_size or 100
        payload = await self._with_rate_limit_retries(
            lambda: order_api.trades(
                sort_by="timestamp",
                limit=limit,
                sort_dir="desc",
                account_index=self._account_index,
                market_id=market_id,
                auth=auth,
            )
        )
        rows = payload.model_dump().get("trades", [])

        if start_at_ms is not None:
            rows = [r for r in rows if int(r.get("timestamp", 0)) * 1000 >= start_at_ms]
        if end_at_ms is not None:
            rows = [r for r in rows if int(r.get("timestamp", 0)) * 1000 <= end_at_ms]

        return {"results": rows, "next": None, "prev": None}

    async def cancel_order_by_client_id(self, client_id: str, market: str | None = None) -> None:
        order = await self.get_order_by_client_id(client_id)
        market_id = int(order["market_index"])
        order_index = int(order["order_index"])
        await self.cancel_order(str(order_index), market_id=market_id)

    async def cancel_order(self, order_id: str, market_id: int | None = None) -> None:
        await self._ensure_clients()
        if market_id is None:
            order = await self.get_order_by_id(order_id)
            market_id = int(order["market_index"])
        assert self._signer is not None

        _tx_info, _tx_hash, err = await self._signer.cancel_order(
            market_index=int(market_id),
            order_index=int(order_id),
            api_key_index=self._api_key_index,
        )
        if err:
            raise RuntimeError(str(err))

    async def modify_order(
        self,
        order_id: str,
        market: str,
        side: str,
        order_type: str,
        size: str,
        price: str,
        trigger_price: str | None,
        _signature_timestamp_ms: int | None,
    ) -> dict[str, Any]:
        del side, _signature_timestamp_ms
        await self._ensure_clients()
        if not self._market_by_id:
            await self._refresh_markets()

        meta = self._resolve_market(market)
        assert self._signer is not None

        order_index = int(str(order_id))
        base_amount, price_int = self._order_ints(meta, size=size, price=price)
        trigger_int = (
            int((Decimal(trigger_price) * (Decimal(10) ** meta.price_decimals)).to_integral_value())
            if trigger_price not in (None, "")
            else 0
        )

        tx_info, tx_response, err = await self._signer.modify_order(
            market_index=meta.market_id,
            order_index=order_index,
            base_amount=base_amount,
            price=price_int,
            trigger_price=trigger_int,
            api_key_index=self._api_key_index,
        )
        if err:
            raise RuntimeError(str(err))

        response_id = None
        if isinstance(tx_response, dict):
            response_id = tx_response.get("tx_hash") or tx_response.get("id")
        elif tx_response is not None:
            response_id = str(tx_response)

        return {
            "order_index": str(order_index),
            "order_id": str(order_index),
            "id": str(response_id) if response_id is not None else str(order_index),
            "market": meta.symbol,
            "market_id": meta.market_id,
            "type": order_type.upper(),
            "size": str(size),
            "price": str(price),
            "trigger_price": str(trigger_price) if trigger_price not in (None, "") else None,
            "tx_info": tx_info.to_dict() if hasattr(tx_info, "to_dict") else None,
            "tx_response": tx_response,
        }

    async def cancel_all_orders(self, market: str | None = None) -> None:
        open_orders = await self.get_open_orders(market)
        for order in open_orders:
            await self.cancel_order(str(order["order_index"]), market_id=int(order["market_index"]))

    async def subscribe_trades(self, _symbol: str) -> None:
        return None

    async def subscribe_orderbook(self, _symbol: str) -> None:
        return None
