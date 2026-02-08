# ------------------------------------------------------------------------------
#  Copyright (c) 2024 Nautilus Technologies, Inc.
#  ------------------------------------------------------------------------------

import hashlib
import hmac
from typing import Any

import msgspec

from nautilus_trader.adapters.http.client import HttpClient
from nautilus_trader.common.clock import LiveClock
from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import ExecClientConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.core.message import Event
from nautilus_trader.execution.client import ExecutionClient
from nautilus_trader.execution.messages import CancelOrder, SubmitOrder, UpdateOrder
from nautilus_trader.model.identifiers import AccountId, ClientOrderId, VenueOrderId
from nautilus_trader.model.orders import Order

from nautilus_trader.adapters.lighter.constants import (
    DEFAULT_CHAIN_ID,
    LIGHTER_HEADER_API_KEY,
    LIGHTER_HEADER_CHAIN_ID,
    LIGHTER_HEADER_SIGNATURE,
    LIGHTER_HEADER_TIMESTAMP,
    LIGHTER_REST_BASE_URL,
    LIGHTER_VENUE,
)
from nautilus_trader.adapters.lighter.factories import LighterInstrumentProvider
from nautilus_trader.adapters.lighter.types import (
    LighterCancelOrderResponse,
    LighterOrderResponse,
)

# Type encoders/decoders
class LighterExecutionClientConfig(ExecClientConfig, kw_only=True):
    """
    Configuration for ``LighterExecutionClient``.
    """

    api_key: str
    api_secret: str
    chain_id: str = DEFAULT_CHAIN_ID


class LighterExecutionClient(ExecutionClient):
    """
    Provides an execution client for the Lighter DEX.
    """

    def __init__(
        self,
        loop: Any,
        msgbus: Any,
        cache: Any,
        clock: LiveClock,
        instrument_provider: LighterInstrumentProvider,
        config: LighterExecutionClientConfig,
    ) -> None:
        super().__init__(
            loop=loop,
            client_id=LighterExecutionClient.__name__,
            venue=LIGHTER_VENUE,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
        )
        self._config = config
        self._api_key = config.api_key
        self._api_secret = config.api_secret
        self._chain_id = config.chain_id
        self._http_client = HttpClient(base_url=LIGHTER_REST_BASE_URL)
        self._instrument_provider = instrument_provider
        self._account_id = AccountId(f"{LIGHTER_VENUE}-{self._api_key[:8]}")

        self._log.info(f"Initializing Lighter Execution Client (account_id={self._account_id}).")

    def _generate_auth_headers(
        self,
        method: str,
        path: str,
        body: str = "",
    ) -> dict[str, str]:
        timestamp = str(self._clock.timestamp_ms())
        message = f"{timestamp}{method}{path}{body}"

        signature = hmac.new(
            key=self._api_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        return {
            LIGHTER_HEADER_CHAIN_ID: self._chain_id,
            LIGHTER_HEADER_API_KEY: self._api_key,
            LIGHTER_HEADER_TIMESTAMP: timestamp,
            LIGHTER_HEADER_SIGNATURE: signature,
        }

    async def _connect(self) -> None:
        self._log.info("Connecting to Lighter Execution Client...")
        # Perform health check or auth check here if needed
        self._set_connected(True)

    async def _disconnect(self) -> None:
        self._log.info("Disconnecting Lighter Execution Client...")
        self._set_connected(False)

    async def _submit_order(self, command: SubmitOrder) -> None:
        order = command.order
        self._log.info(f"Submitting order: {order}")

        instrument = self._instrument_provider.find(order.instrument_id)
        if instrument is None:
            self._log.error(f"Instrument not found: {order.instrument_id}")
            return

        # Map Nautilus Order to Lighter Request
        payload = {
            "chainId": self._chain_id,
            "symbol": instrument.symbol.value, # BASE-QUOTE format
            "side": "BUY" if order.side.is_buy else "SELL",
            "type": "LIMIT" if order.order_type.is_limit else "MARKET",
            "price": str(order.price),
            "quantity": str(order.quantity),
            "clientOrderId": order.client_order_id.value,
            "tif": "GTC",  # Nautilus typically defaults to GTC
        }

        path = "/v1/order"
        body_str = msgspec.json.encode(payload).decode("utf-8")
        headers = self._generate_auth_headers("POST", path, body_str)

        try:
            response = await self._http_client.post(
                path=path,
                headers=headers,
                data=body_str,
            )
            resp_data = msgspec.json.decode(response.data)
            result = msgspec.to_builtins(resp_data)
            # Process result and emit OrderAccepted
            self._log.info(f"Order response: {result}")
            # TODO: Handle state transition
        except Exception as e:
            self._log.error(f"Error submitting order: {e}")

    async def _cancel_order(self, command: CancelOrder) -> None:
        self._log.info(f"Canceling order: {command}")
        # Implementation for cancellation
        # Assuming DELETE /v1/order

    async def _modify_order(self, command: UpdateOrder) -> None:
        self._log.info(f"Modifying order: {command}")
        # Implementation for modification

    async def _generate_order_status(self, venue_order_id: VenueOrderId) -> None:
        pass

    async def _update_account_state(self) -> None:
        pass
