# ------------------------------------------------------------------------------
#  Copyright (c) 2024 Nautilus Technologies, Inc.
#  ------------------------------------------------------------------------------

from nautilus_trader.model.identifiers import Venue

LIGHTER_VENUE = Venue("LIGHTER")

# REST API
LIGHTER_REST_BASE_URL = "https://api.lighter.xyz"
LIGHTER_API_VERSION = "v1"

# WebSocket API
LIGHTER_WS_PUBLIC_URL = "wss://api.lighter.xyz/ws"
LIGHTER_WS_PRIVATE_URL = "wss://api.lighter.xyz/ws"

# Headers
LIGHTER_HEADER_CHAIN_ID = "x-lighter-chain-id"
LIGHTER_HEADER_API_KEY = "x-api-key"
LIGHTER_HEADER_TIMESTAMP = "x-timestamp"
LIGHTER_HEADER_SIGNATURE = "x-signature"

# Defaults
DEFAULT_CHAIN_ID = "137"  # Polygon Mainnet
