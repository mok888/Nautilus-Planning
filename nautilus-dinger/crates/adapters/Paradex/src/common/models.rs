use serde::{Deserialize, Serialize};

/// A generic WebSocket or REST API message from Paradex.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexMessage {
    pub id: String,
}

/// Market information returned by GET /markets.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexMarketInfo {
    pub symbol: String,
    pub base_currency: String,
    pub quote_currency: String,
    pub settlement_currency: String,
    pub order_size_increment: String,
    pub price_tick_size: String,
    pub min_notional: String,
    pub open_at: Option<u64>,
    pub expiry_at: u64,
    pub asset_kind: String,
    pub market_kind: String,
}

/// Token information returned by GET /info.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ParadexTokenInfo {
    pub token_id: u32,
    pub symbol: String,
    pub decimals: u32,
    pub mint_addr: String,
    pub weight_bps: u32,
}

/// Response from GET /markets endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexInfoResponse {
    pub results: Vec<ParadexMarketInfo>,
}

/// Orderbook entry (bid or ask).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexOrderbookLevel {
    pub price: String,
    pub size: String,
}

/// Response from GET /market/{id}/orderbook.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexOrderbookResponse {
    pub asks: Vec<ParadexOrderbookLevel>,
    pub bids: Vec<ParadexOrderbookLevel>,
    pub timestamp: Option<u64>,
    pub seq_num: Option<u64>,
    pub last_updated_at: Option<u64>,
}

/// A single trade from GET /trades.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexTrade {
    pub price: String,
    pub size: String,
    pub side: String,
    pub timestamp: u64,
}

/// Response from GET /trades.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexTradesResponse {
    pub trades: Vec<ParadexTrade>,
}

/// Response from POST /action (transaction submission).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexActionResponse {
    pub action_id: Option<String>,
    pub status: Option<String>,
    pub tx_signature: Option<String>,
    pub id: Option<String>,
    pub client_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexOrderResponse {
    pub id: Option<String>,
    pub client_id: Option<String>,
    pub market: Option<String>,
    pub side: Option<String>,
    #[serde(rename = "type")]
    pub order_type: Option<String>,
    pub status: Option<String>,
    pub instruction: Option<String>,
    pub size: Option<String>,
    pub remaining_size: Option<String>,
    pub price: Option<String>,
    pub trigger_price: Option<String>,
    pub avg_fill_price: Option<String>,
    pub cancel_reason: Option<String>,
    pub created_at: Option<u64>,
    pub last_updated_at: Option<u64>,
    #[serde(default)]
    pub flags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexOrdersResponse {
    pub results: Vec<ParadexOrderResponse>,
    pub next: Option<String>,
    pub prev: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexFillResponse {
    pub id: Option<String>,
    pub order_id: Option<String>,
    pub client_id: Option<String>,
    pub market: Option<String>,
    pub side: Option<String>,
    pub size: Option<String>,
    pub price: Option<String>,
    pub fee: Option<String>,
    pub fee_currency: Option<String>,
    pub liquidity: Option<String>,
    pub created_at: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexFillsResponse {
    pub results: Vec<ParadexFillResponse>,
    pub next: Option<String>,
    pub prev: Option<String>,
}
