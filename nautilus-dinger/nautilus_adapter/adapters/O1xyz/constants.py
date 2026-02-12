from nautilus_trader.model.identifiers import Venue

VENUE = Venue("O1_XYZ")

# REST API URLs
REST_URL_MAINNET = "https://zo-mainnet.n1.xyz"
REST_URL_TESTNET = "https://zo-devnet.n1.xyz"

# WebSocket URLs
WS_URL_PUBLIC = "wss://api.o1.exchange/ws"
WS_URL_PRIVATE = "wss://api.o1.exchange/ws"

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
