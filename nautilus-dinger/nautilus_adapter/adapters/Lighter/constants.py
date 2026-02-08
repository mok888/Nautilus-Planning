from nautilus_trader.model.identifiers import Venue

VENUE = Venue("LIGHTER")

# Standardized Venue Constants
DEFAULT_HTTP_REQUEST_TIMEOUT_SECS = 10
MAX_RETRIES = 3
RETRY_DELAY_SECS = 1.0

# WebSocket Limits
WS_MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB
WS_PING_INTERVAL_SECS = 20
