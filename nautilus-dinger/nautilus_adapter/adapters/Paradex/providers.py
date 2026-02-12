import asyncio
import json
import time
from decimal import Decimal

from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.model.identifiers import InstrumentId, Symbol
from nautilus_trader.model.instruments import CryptoPerpetual, Instrument
from nautilus_trader.model.objects import Currency, Price, Quantity

from .constants import REST_URL_MAINNET, VENUE


class ParadexInstrumentProvider(InstrumentProvider):
    """
    Instrument provider for Paradex exchange.

    Fetches available markets from the /info endpoint and converts them
    to NautilusTrader Instrument objects. Market data includes:
    - symbol (e.g., BTCUSD, ETHUSD, SOLUSD)
    - priceDecimals and sizeDecimals (dynamic per market)
    - imf, mmf, cmf (margin factors)
    """

    def __init__(self, client: object | None = None):
        super().__init__(config=InstrumentProviderConfig(load_all=True))
        self._client = client
        self._base_url = REST_URL_MAINNET

    def find(self, instrument_id: InstrumentId) -> Instrument | None:
        """
        Find an instrument by its identifier.
        """
        return super().find(instrument_id)

    @staticmethod
    def _precision_from_increment(value: str) -> int:
        normalized = Decimal(value).normalize()
        exponent = int(normalized.as_tuple().exponent)
        return abs(exponent) if exponent < 0 else 0

    @staticmethod
    def _build_instrument(market: dict) -> CryptoPerpetual:
        symbol_value = str(market["symbol"])
        base_code = str(market.get("base_currency") or "BTC")
        quote_code = str(market.get("quote_currency") or "USD")
        settlement_code = str(market.get("settlement_currency") or quote_code)
        size_increment = str(market.get("order_size_increment") or "0.001")
        price_increment = str(market.get("price_tick_size") or "0.1")

        ts_now = time.time_ns()
        return CryptoPerpetual(
            instrument_id=InstrumentId(Symbol(symbol_value), VENUE),
            raw_symbol=Symbol(symbol_value),
            base_currency=Currency.from_str(base_code),
            quote_currency=Currency.from_str(quote_code),
            settlement_currency=Currency.from_str(settlement_code),
            is_inverse=False,
            price_precision=ParadexInstrumentProvider._precision_from_increment(price_increment),
            size_precision=ParadexInstrumentProvider._precision_from_increment(size_increment),
            price_increment=Price.from_str(price_increment),
            size_increment=Quantity.from_str(size_increment),
            ts_event=ts_now,
            ts_init=ts_now,
            info=market,
        )

    async def load_all_async(self, filters: dict | None = None) -> None:
        _ = filters
        if self._client is None or not hasattr(self._client, "get_info"):
            raise RuntimeError("Paradex instrument provider client is not configured")

        loop = asyncio.get_running_loop()
        raw_info = await loop.run_in_executor(None, self._client.get_info)
        parsed = json.loads(raw_info) if isinstance(raw_info, str) else raw_info
        markets = parsed.get("results", []) if isinstance(parsed, dict) else []

        self._instruments.clear()
        self._currencies.clear()

        for market in markets:
            try:
                instrument = self._build_instrument(market)
                self.add_currency(instrument.base_currency)
                self.add_currency(instrument.quote_currency)
                self.add_currency(instrument.settlement_currency)
                self.add(instrument)
            except Exception as e:
                self._log.warning(
                    f"Skipping invalid Paradex market payload: {market} ({e})",
                )

    async def load_ids_async(
        self,
        instrument_ids: list[InstrumentId],
        filters: dict | None = None,
    ) -> None:
        PyCondition.not_none(instrument_ids, "instrument_ids")
        if not instrument_ids:
            return

        await self.load_all_async(filters)

        missing = [i for i in instrument_ids if self.find(i) is None]
        if missing:
            missing_str = ", ".join(i.value for i in missing)
            self._log.warning(f"Unable to load Paradex instruments: {missing_str}")

    async def load_async(
        self,
        instrument_id: InstrumentId,
        filters: dict | None = None,
    ) -> None:
        PyCondition.not_none(instrument_id, "instrument_id")
        await self.load_ids_async([instrument_id], filters)
