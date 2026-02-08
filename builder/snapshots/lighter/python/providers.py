# ------------------------------------------------------------------------------
#  Copyright (c) 2024 Nautilus Technologies, Inc.
#  ------------------------------------------------------------------------------

from nautilus_trader.adapters.lighter.config import LighterInstrumentProviderConfig
from nautilus_trader.adapters.lighter.constants import LIGHTER_REST_BASE_URL, LIGHTER_VENUE
from nautilus_trader.adapters.http.client import HttpClient
from nautilus_trader.model.currencies import USD, ETH, BTC, USDC
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.identifiers import InstrumentId, Symbol
from nautilus_trader.model.instruments import Instrument

import msgspec


class LighterInstrumentProvider:
    """
    Provides a means of loading `Instrument` objects from Lighter.
    """

    def __init__(
        self,
        config: LighterInstrumentProviderConfig,
    ) -> None:
        self._config = config
        self._http_client = HttpClient(base_url=LIGHTER_REST_BASE_URL)
        self._chain_id = config.chain_id

    async def load_all_async(self) -> list[Instrument]:
        instruments = []
        try:
            # Requesting tickers to discover instruments
            response = await self._http_client.get(
                path="/v1/tickers",
                params={"chainId": self._chain_id},
            )
            data = msgspec.json.decode(response.data)

            for item in data:
                # Assuming data structure based on schema: symbol, lastPrice, volume, priceStep, sizeStep
                symbol_str = item.get("symbol")
                price_precision = self._extract_precision(item.get("priceStep"))
                size_precision = self._extract_precision(item.get("sizeStep"))

                # Parse BASE-QUOTE format
                parts = symbol_str.split("-")
                if len(parts) != 2:
                    continue

                base_currency = parts[0].upper()
                quote_currency = parts[1].upper()

                # Basic creation of Instrument (using generic Instrument or specific spot type)
                # In Nautilus, typically CurrencyPair for spot
                instrument_id = InstrumentId(symbol=Symbol(symbol_str), venue=LIGHTER_VENUE)

                # This is a simplified instantiation for the placeholder.
                # A full implementation would parse price/size steps into Price/Quantity types.
                # and handle currency mappings properly.
                # instrument = CurrencyPair(...)
                # instruments.append(instrument)
                pass

        except Exception as e:
            print(f"Failed to load instruments: {e}")

        return instruments

    def _extract_precision(self, step_str: str | None) -> int:
        if not step_str:
            return 8  # Default from schema
        step = float(step_str)
        return 8  # Simplified logic

    def find(self, instrument_id: InstrumentId) -> Instrument | None:
        # Synchronous helper
        return None
