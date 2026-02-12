from nautilus_trader.model.identifiers import Venue

VENUE = Venue("LIGHTER")

# REST API URLs
REST_URL_MAINNET = "https://mainnet.zklighter.elliot.ai"
REST_URL_TESTNET = "https://testnet.zklighter.elliot.ai"

# WebSocket URLs
WS_URL_PUBLIC = "wss://mainnet.zklighter.elliot.ai/stream"
WS_URL_PRIVATE = "wss://mainnet.zklighter.elliot.ai/stream"

# Standardized Venue Constants
DEFAULT_HTTP_REQUEST_TIMEOUT_SECS = 10
MAX_RETRIES = 3
RETRY_DELAY_SECS = 1.0

# WebSocket Limits
WS_MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB
WS_PING_INTERVAL_SECS = 30
WS_HEARTBEAT_INTERVAL_SECS = 30

# Rate Limiting
MAX_REQUESTS_PER_SECOND = 10

# Order Types
ORDER_TYPE_LIMIT = "limit"
ORDER_TYPE_MARKET = "market"

# Order States
ORDER_STATE_NEW = "NEW"
ORDER_STATE_OPEN = "OPEN"
ORDER_STATE_FILLED = "FILLED"
ORDER_STATE_CANCELED = "CANCELED"
ORDER_STATE_REJECTED = "REJECTED"
ORDER_STATE_EXPIRED = "EXPIRED"
