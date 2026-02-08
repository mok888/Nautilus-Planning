# Exchange Overview
- Launch year: 2023
- Exchange type: DEX (Hyperliquid L1)
- Supported markets: Perps (USDC margined)

# API Structure
- REST base URLs: https://api.hyperliquid.xyz
- WebSocket URLs: wss://api.hyperliquid.xyz/ws
- API versioning scheme: None explicit, assumes v1

# Authentication
- Auth method: Arbitrum Wallet Signature (EIP-712) for ordering, None for public data
- Required headers: Content-Type: application/json
- Timestamp rules: ms timestamps required in payloads

# Rate Limits
- REST limits: 1200 requests/ minute (IP based)
- WebSocket limits: None explicit, but aggressive connection pruning

# Order Endpoints
- path: /exchange
- method: POST
- purpose: Place, modify, or cancel orders

# WebSocket Feeds
- Orderbook channels: "l2Book"
- Trade channels: "trades"
- Account channels: "fills"

# Order Lifecycle Notes
- Order states: Open, Filled, Canceled, Triggered
- Cancel behavior: Supports "Cloid" (Client Order ID) cancellation
- Partial fills: Supported

# Special Notes
- Uses msgpack for internal data structures in some cases but API is JSON.
- Requires signing via specific EIP-712 types.
