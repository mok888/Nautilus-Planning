from decimal import Decimal


def compute_quantity_from_risk(
    free_balance: Decimal,
    risk_pct: Decimal,
    leverage: Decimal,
    reference_price: Decimal,
) -> Decimal:
    if reference_price <= Decimal("0"):
        raise ValueError("Reference price must be positive for risk sizing")
    if risk_pct <= Decimal("0"):
        raise ValueError("risk_pct must be positive")
    if leverage <= Decimal("0"):
        raise ValueError("leverage must be positive")

    risk_capital = free_balance * (risk_pct / Decimal("100"))
    notional = risk_capital * leverage
    quantity = notional / reference_price
    if quantity <= Decimal("0"):
        raise ValueError("Computed quantity is non-positive")
    return quantity


def resolve_canonical_symbol(symbol: str, available_symbols: list[str], venue: str) -> str:
    if not available_symbols:
        raise RuntimeError(f"{venue} market list is empty")

    requested = symbol.upper()
    by_upper = {s.upper(): s for s in available_symbols}
    if requested in by_upper:
        return by_upper[requested]

    requested_key = _symbol_key(symbol)
    for candidate in available_symbols:
        if _symbol_key(candidate) == requested_key:
            return candidate

    suggestions = sorted(available_symbols)[:12]
    raise RuntimeError(
        f"Unsupported {venue} symbol '{symbol}'. Sample supported symbols: {', '.join(suggestions)}",
    )


def _symbol_key(value: str) -> str:
    s = value.upper().replace("/", "").replace("-", "").replace("_", "")
    if s.endswith("PERP"):
        s = s[:-4]
    if s.endswith("USDC"):
        s = s[:-4]
    if s.endswith("USD"):
        s = s[:-3]
    return s
