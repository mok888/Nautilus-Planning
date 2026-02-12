import asyncio

from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument

from .constants import REST_URL_MAINNET


class EdgexInstrumentProvider(InstrumentProvider):
    """
    Instrument provider for Edgex exchange.

    Fetches available markets from the /info endpoint and converts them
    to NautilusTrader Instrument objects. Market data includes:
    - symbol (e.g., BTCUSD, ETHUSD, SOLUSD)
    - priceDecimals and sizeDecimals (dynamic per market)
    - imf, mmf, cmf (margin factors)
    """

    def __init__(self):
        super().__init__()
        self._base_url = REST_URL_MAINNET

    async def initialize(self) -> None:
        """
        Initialize the provider by fetching instruments from the /info endpoint.
        """
        pass

    def find(self, instrument_id: InstrumentId) -> Instrument | None:
        """
        Find an instrument by its identifier.
        """
        return super().find(instrument_id)

    async def load_all(self, reload: bool = False) -> None:
        """
        Load all available instruments from Edgex.

        Fetches from GET /info and parses the markets array.
        Each market has: marketId, symbol, priceDecimals, sizeDecimals.
        """
        pass
