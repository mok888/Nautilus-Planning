from nautilus_trader.model.objects import Money
from nautilus_trader.accounting.account_state import AccountState

def to_account_state(snapshot, currency):
    """
    Convert a RiskSnapshot object (from Rust/JSON) to a Nautilus AccountState.
    """
    return AccountState(
        equity=Money(snapshot.equity, currency),
        balance=Money(snapshot.balance, currency),
        margin_used=Money(snapshot.margin_used, currency),
        margin_available=Money(snapshot.margin_available, currency),
        unrealized_pnl=Money(snapshot.unrealized_pnl, currency),
    )
