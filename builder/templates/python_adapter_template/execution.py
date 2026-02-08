import asyncio

from nautilus_trader.common.component import MessageBus
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import NautilusConfig
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.identifiers import ClientId, Venue
from nautilus_trader.model.enums import OmsType, AccountType
from nautilus_trader.model.objects import Currency
from nautilus_trader.execution.messages import SubmitOrder, CancelOrder
from nautilus_trader.execution.reports import (
    OrderStatusReport, 
    FillReport, 
    PositionStatusReport, 
    ExecutionMassStatus
)

class {{EXCHANGE_NAME}}ExecutionClient(LiveExecutionClient):
    """
    A compliant reference implementation for a NautilusTrader Execution Client.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client: object, # The Rust HTTP client
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

    async def _connect(self) -> None:
        """
        Connect to the execution interface.
        """
        pass

    async def _disconnect(self) -> None:
        """
        Disconnect from the execution interface.
        """
        pass

    async def _submit_order(self, command: SubmitOrder) -> None:
        """
        Submit an order to the venue.
        """
        pass

    async def _cancel_order(self, command: CancelOrder) -> None:
        """
        Cancel an order at the venue.
        """
        pass

    async def _cancel_all_orders(self, command) -> None:
        pass
        
    async def _modify_order(self, command) -> None:
        pass
        
    async def _batch_cancel_orders(self, command) -> None:
        pass
        
    async def _submit_order_list(self, command) -> None:
        pass

    async def generate_order_status_report(self, command) -> OrderStatusReport | None:
        return None

    async def generate_order_status_reports(self, command) -> list[OrderStatusReport]:
        return []

    async def generate_fill_reports(self, command) -> list[FillReport]:
        return []

    async def generate_position_status_reports(self, command) -> list[PositionStatusReport]:
        return []

    async def generate_mass_status(self, lookback_mins: int | None = None) -> ExecutionMassStatus | None:
        return None
