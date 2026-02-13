import asyncio
import time
from decimal import Decimal

from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.model.identifiers import InstrumentId, Symbol
from nautilus_trader.model.instruments import CryptoPerpetual, Instrument
from nautilus_trader.model.objects import Currency, Price, Quantity

from .constants import VENUE


class LighterInstrumentProvider(InstrumentProvider):
    def __init__(self, client: object | None = None):
        super().__init__(config=InstrumentProviderConfig(load_all=True))
        self._client = client

    def find(self, instrument_id: InstrumentId) -> Instrument | None:
        return super().find(instrument_id)

    @staticmethod
    def _precision_from_increment(value: str) -> int:
        normalized = Decimal(value).normalize()
        exponent = int(normalized.as_tuple().exponent)
        return abs(exponent) if exponent < 0 else 0

    @staticmethod
    def _symbol_to_nautilus(symbol: str) -> str:
        upper = symbol.upper()
        if upper.endswith("PERP"):
            upper = upper[:-4]
        return f"{upper}-USD-PERP"

    @classmethod
    def _build_instrument(cls, market: dict) -> CryptoPerpetual:
        symbol_raw = str(market.get("symbol") or "BTC")
        symbol_value = cls._symbol_to_nautilus(symbol_raw)

        size_decimals = int(market.get("size_decimals", market.get("supported_size_decimals", 5)))
        price_decimals = int(
            market.get("price_decimals", market.get("supported_price_decimals", 1))
        )

        size_increment = str(Decimal(1) / (Decimal(10) ** size_decimals))
        price_increment = str(Decimal(1) / (Decimal(10) ** price_decimals))

        ts_now = time.time_ns()

        return CryptoPerpetual(
            instrument_id=InstrumentId(Symbol(symbol_value), VENUE),
            raw_symbol=Symbol(symbol_raw),
            base_currency=Currency.from_str(symbol_raw.upper()),
            quote_currency=Currency.from_str("USD"),
            settlement_currency=Currency.from_str("USD"),
            is_inverse=False,
            price_precision=cls._precision_from_increment(price_increment),
            size_precision=cls._precision_from_increment(size_increment),
            price_increment=Price.from_str(price_increment),
            size_increment=Quantity.from_str(size_increment),
            ts_event=ts_now,
            ts_init=ts_now,
            info=market,
        )

    async def load_all_async(self, filters: dict | None = None) -> None:
        _ = filters
        if self._client is None or not hasattr(self._client, "get_info"):
            raise RuntimeError("Lighter instrument provider client is not configured")

        data = self._client.get_info()
        if asyncio.iscoroutine(data):
            data = await data
        markets = data.get("results", []) if isinstance(data, dict) else []

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
                self._log.warning(f"Skipping invalid Lighter market payload: {market} ({e})")

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
            self._log.warning(f"Unable to load Lighter instruments: {missing_str}")

    async def load_async(
        self,
        instrument_id: InstrumentId,
        filters: dict | None = None,
    ) -> None:
        PyCondition.not_none(instrument_id, "instrument_id")
        await self.load_ids_async([instrument_id], filters)
