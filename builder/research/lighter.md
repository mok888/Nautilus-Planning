# Lighter DEX Research Report

## Exchange Overview

- **Launch year**: Not explicitly documented in available sources (whitepaper dated October 2025)
- **Exchange type**: DEX (Decentralized Exchange) - Built as a ZK-rollup on Ethereum
- **Supported markets**: Perpetual futures, spot trading, public pools, real-world assets (RWA)

Source: https://docs.lighter.xyz/perpetual-futures/order-types-and-matching, https://assets.lighter.xyz/whitepaper.pdf

## API Structure

- **REST base URLs**:
  - Mainnet: `https://mainnet.zklighter.elliot.ai`
  - Testnet: `https://testnet.zklighter.elliot.ai`

- **WebSocket URLs**:
  - Mainnet: `wss://mainnet.zklighter.elliot.ai/stream`
  - Testnet: `wss://testnet.zklighter.elliot.ai/stream`
  - Read-only mode: `wss://mainnet.zklighter.elliot.ai/stream?readonly=true`

- **API versioning scheme**: v1.0 (current version)

Source: https://apidocs.lighter.xyz/docs/get-started, https://apidocs.lighter.xyz/docs/websocket-reference

## Authentication

- **Auth method**: API key index + private key signature using SignerClient
  - Each API key has a public and private key pair
  - Transactions are signed using Schnorr signature scheme

- **Required headers**:
  - For REST API: `auth` token generated via `create_auth_token_with_expiry()`
  - For WebSocket: `auth` parameter in subscription messages

- **Timestamp rules**:
  - Uses `ExpiredAt` timestamp (milliseconds)
  - Nonce management is per API_KEY index
  - Nonce must be incremented for each transaction

Source: https://apidocs.lighter.xyz/docs/api-keys, https://apidocs.lighter.xyz/docs/nonce-management

## Rate Limits

- **REST API limits**:
  - Premium Account: 24,000 weighted REST API requests per minute window
  - Standard Account: 60 weighted requests per minute window

- **WebSocket limits**:
  - Shares the same rate limits as REST API
  - Applied on both IP address and L1 wallet address

- **Additional limits**:
  - `sendTx` and `sendTxBatch` transactions can increase volume quota
  - Maximum 50 transactions allowed per batch
  - Maximum 10 API tokens per account

Source: https://apidocs.lighter.xyz/docs/rate-limits, https://apidocs.lighter.xyz/docs/data-structures-constants-and-errors

## Order Endpoints

### Transaction Endpoints

| Path | Method | Purpose |
|-------|--------|---------|
| `/api/v1/sendTx` | POST | Submit a signed transaction |
| `/api/v1/sendTxBatch` | POST | Submit up to 50 transactions in batch |
| `/api/v1/nextNonce` | GET | Get next nonce for specific account and API key |
| `/api/v1/tx` | GET | Get transaction details |
| `/api/v1/txs` | GET | Get list of transactions |

### Account Endpoints

| Path | Method | Purpose |
|-------|--------|---------|
| `/api/v1/account` | GET | Get account by account index or L1 address |
| `/api/v1/accountsByL1Address` | GET | Get all accounts (master and sub-accounts) for L1 wallet |
| `/api/v1/accountActiveOrders` | GET | Get account active orders (requires auth) |
| `/api/v1/accountInactiveOrders` | GET | Get account inactive orders |
| `/api/v1/accountLimits` | GET | Get account limits |
| `/api/v1/pnl` | GET | Get profit and loss data |
| `/api/v1/changeAccountTier` | POST | Change account tier |

### Order/Market Data Endpoints

| Path | Method | Purpose |
|-------|--------|---------|
| `/api/v1/orderBooks` | GET | Get all order books metadata |
| `/api/v1/orderBookDetails` | GET | Get order book details for specific market |
| `/api/v1/orderBookOrders` | GET | Get orders from order book |
| `/api/v1/recentTrades` | GET | Get recent trades |
| `/api/v1/trades` | GET | Get trade history |
| `/api/v1/export` | GET | Export account data |

### API Key Management

| Path | Method | Purpose |
|-------|--------|---------|
| `/api/v1/apikeys` | GET | Get API key data |
| `/api/v1/tokens_create` | POST | Create new API token |
| `/api/v1/tokens` | GET | Get all API tokens |
| `/api/v1/tokens_revoke` | POST | Revoke API token |

### Additional Endpoints

| Path | Method | Purpose |
|-------|--------|---------|
| `/api/v1/candles` | GET | Get candlestick data |
| `/api/v1/fundings` | GET | Get funding payment history |
| `/api/v1/funding-rates` | GET | Get funding rates |
| `/api/v1/deposit_history` | GET | Get deposit history |
| `/api/v1/transfer_history` | GET | Get transfer history |
| `/api/v1/withdraw_history` | GET | Get withdrawal history |
| `/api/v1/fastwithdraw` | POST | Fast withdrawal |
| `/api/v1/createIntentAddress` | POST | Create bridge intent address |

Source: https://apidocs.lighter.xyz/reference, https://apidocs.lighter.xyz/reference/account-1

## WebSocket Feeds

### Orderbook Channels

- **`order_book/{MARKET_INDEX}`**: Sends new ask and bid orders for given market in batches every 50ms
  - Sends complete snapshot on subscription
  - Only state changes after subscription
  - Contains `nonce` and `begin_nonce` for continuity verification

- **Response structure**:
```json
{
  "channel": "order_book:{MARKET_INDEX}",
  "offset": INTEGER,
  "order_book": {
    "code": INTEGER,
    "asks": [{"price": STRING, "size": STRING}],
    "bids": [{"price": STRING, "size": STRING}],
    "nonce": INTEGER,
    "begin_nonce": INTEGER
  },
  "timestamp": INTEGER,
  "type": "update/order_book"
}
```

### Trade Channels

- **`trade/{MARKET_INDEX}`**: Sends new trade data for given market
  - Contains `trade_id`, `tx_hash`, `size`, `price`, `usd_amount`
  - Includes both maker and taker account IDs

### Account Channels

- **`account_all/{ACCOUNT_ID}`**: Sends specific account market data for all markets
  - Includes assets, positions, trades, funding histories
  - Reconnects and receives new snapshot on new subscription

- **`account_market/{MARKET_ID}/{ACCOUNT_ID}`**: Specific account market data (requires auth)
  - Returns assets, orders, position, trades
  - For perpetuals: assets is null, funding_history present
  - For spot: assets present, funding_history is null

- **`account_all_orders/{ACCOUNT_ID}`**: All orders of an account (requires auth)
- **`account_orders/{MARKET_INDEX}/{ACCOUNT_ID}`**: Orders on specific market (requires auth)
- **`account_all_trades/{ACCOUNT_ID}`**: All trades of an account (requires auth)
- **`account_all_positions/{ACCOUNT_ID}`**: All positions (requires auth)
- **`account_all_assets/{ACCOUNT_ID}`**: All spot market assets (requires auth)

### Market Stats Channels

- **`market_stats/{MARKET_INDEX}`**: Market stat data for given market
  - Includes `index_price`, `mark_price`, `open_interest`, `funding_rate`
  - Can use `all` to get all markets

- **`spot_market_stats/{MARKET_INDEX}`**: Spot market stats
  - Includes `mid_price`, `last_trade_price`, daily volume and price changes

### Other Channels

- **`user_stats/{ACCOUNT_ID}`**: Account stats (collateral, portfolio value, leverage)
- **`account_tx/{ACCOUNT_ID}`**: Transaction updates (requires auth)
- **`height`**: Blockchain height updates
- **`pool_data/{ACCOUNT_ID}`**: Pool activities (trades, orders, positions, shares)
- **`pool_info/{ACCOUNT_ID}`**: Pool information (APY, share prices)
- **`notification/{ACCOUNT_ID}`**: Notifications (liquidation, deleverage, announcement)

Source: https://apidocs.lighter.xyz/docs/websocket-reference

## Order Lifecycle Notes

### Order States

```go
const (
    InProgressOrder         // In register
    PendingOrder            // Pending to be triggered
    ActiveLimitOrder        // Active limit order
    FilledOrder             // Filled (3)
    CanceledOrder           // Canceled (4)
    CanceledOrder_PostOnly                     // 5
    CanceledOrder_ReduceOnly                   // 6
    CanceledOrder_PositionNotAllowed              // 7
    CanceledOrder_MarginNotAllowed              // 8
    CanceledOrder_TooMuchSlippage             // 9
    CanceledOrder_NotEnoughLiquidity           // 10
    CanceledOrder_SelfTrade                   // 11
    CanceledOrder_Expired                     // 12
    CanceledOrder_OCO                        // 13
    CanceledOrder_Child                      // 14
    CanceledOrder_Liquidation                 // 15
    CanceledOrder_InvalidBalance              // 16
)
```

### Order Types

```go
const (
    LimitOrder           = iota  // 0
    MarketOrder          = 1
    StopLossOrder        = 2
    StopLossLimitOrder   = 3
    TakeProfitOrder      = 4
    TakeProfitLimitOrder = 5
    TWAPOrder            = 6
    // Internal types
    TWAPSubOrder         = 7
    LiquidationOrder      = 8
)
```

### Time in Force Types

```go
const (
    ImmediateOrCancel = iota  // 0
    GoodTillTime      = 1          // GTC
    PostOnly          = 2           // Post-Only
)
```

### Cancel Behavior

- Cancel using `order_index` or `client_order_index`
- Cancelling a partially filled order results in entire order status as `CANCELLED`
- Already filled portion remains as completed trade in trade history
- Remaining unfilled portion is cancelled

### Partial Fills

- Order includes `remaining_base_amount` and `filled_base_amount`
- Partial fills reduce `remaining_base_amount`
- Order can be in `Filled` status only when fully executed
- Partially filled orders continue to be active

### Order Execution Notes

- Maker orders with correct syntax can still fail at API level if conditions aren't met (e.g., not enough margin)
- In this case, nonce does NOT increase
- Taker orders go through regardless as long as syntax is correct
- If sequencer rejects order (e.g., incorrect price), order is cancelled and nonce increases
- Exception: Order not executed by sequencer before `ExpiredAt` timestamp

Source: https://github.com/elliottech/lighter-go/blob/master/types/txtypes/constants.go, https://apidocs.lighter.xyz/docs/data-structures-constants-and-errors, https://apidocs.lighter.xyz/docs/trading

## Special Notes

### Non-Standard Behavior

1. **Nonces are per API_KEY**: Each of 255 possible API key indices (0-254) manages its own nonce stream independently, allowing parallel transaction submission
   - Indices 0-1 are reserved for web/mobile interfaces

2. **SDK handles auto-increment**: The Python SDK handles nonce management automatically. For complex systems, implement local nonce management.

3. **Price interpretation**: When specifying a price for taker orders, it's interpreted as the "worst price" you're willing to accept. If sequencer cannot offer equal or better price, order is cancelled.

4. **TP/SL slippage**: For TP/SL orders, indicate both trigger price AND price parameter. The price parameter indicates allowed slippage for execution.

5. **Decimal precision**:
   - Use `orderBookDetails` endpoint to get decimal precision per market
   - `supported_size_decimals`: number of decimals for order size
   - `supported_price_decimals`: number of decimals for order price
   - `min_base_amount`: minimum base token for single order
   - `min_quote_amount`: minimum quote token (USDC) for single order

6. **Order book nonce vs offset**:
   - `nonce` is tied to Lighter's matching engine
   - `offset` is tied to API servers
   - On reconnection, `offset` may change drastically if routed to different server
   - Each update increases `offset`, but not guaranteed to be continuous

7. **Batch transactions**: Up to 50 transactions in single message via `sendTxBatch`

8. **Client Order Index**:
   - `client_order_index` is user-provided unique identifier (uint48)
   - Used to reference orders later (e.g., for cancellation)
   - If missing, can use `trade_id` (assigned by exchange)

9. **Maker vs Taker fee handling**: Taker orders always go through with correct syntax. Maker orders can fail at API level due to margin/conditions.

10. **Self-trade prevention**: Built-in self-trade prevention mechanisms

Source: https://apidocs.lighter.xyz/docs/nonce-management, https://apidocs.lighter.xyz/docs/trading, https://docs.lighter.xyz/perpetual-futures/self-trade-prevention

### Known Quirks

1. **Timestamp inconsistencies**: SDK shows timestamps in both milliseconds and seconds in different places (GitHub issue #115)

2. **No single order status endpoint**: Need `fetch_order` routine to query state of individual orders (GitHub issue #31)

3. **Minimum order amounts**: Apply only to maker orders, not taker orders

4. **API success ≠ execution**: HTTP 200 only confirms syntax correctness, not order execution. Monitor via WebSocket for actual execution.

5. **Limited order modification**: Can only modify `base_amount` and `price`, not order type or time in force

Source: https://github.com/elliottech/lighter-python/issues/115, https://github.com/elliottech/lighter-python/issues/31

---

**Documentation Sources**:
- Main API Docs: https://apidocs.lighter.xyz/docs/get-started
- WebSocket Reference: https://apidocs.lighter.xyz/docs/websocket-reference
- Data Structures: https://apidocs.lighter.xyz/docs/data-structures-constants-and-errors
- Rate Limits: https://apidocs.lighter.xyz/docs/rate-limits
- Whitepaper: https://assets.lighter.xyz/whitepaper.pdf
- Python SDK: https://github.com/elliottech/lighter-python
- Go SDK: https://github.com/elliottech/lighter-go
- Official Docs: https://docs.lighter.xyz/trading/api
