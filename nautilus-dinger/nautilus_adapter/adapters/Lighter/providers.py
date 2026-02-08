import asyncio

from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument

class LighterInstrumentProvider(InstrumentProvider):
    """
    Instrument provider for Lighter.
    """

    async def initialize(self) -> None:
        """
        Initialize the provider by fetching instruments from the exchange.
        """
        pass
    
    def find(self, instrument_id: InstrumentId) -> Instrument | None:
        return super().find(instrument_id)
        
    async def load_all(self, reload: bool = False) -> None:
        pass
