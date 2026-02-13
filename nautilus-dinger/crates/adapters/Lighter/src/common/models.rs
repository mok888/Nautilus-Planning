use serde::{Deserialize, Serialize};

/// A generic WebSocket or REST API message from Lighter.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterMessage {
    pub id: String,
}

/// Market information returned by GET /info.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LighterMarketInfo {
    pub market_id: u32,
    pub symbol: String,
    pub price_decimals: u32,
    pub size_decimals: u32,
    pub base_token_id: u32,
    pub quote_token_id: u32,
    pub imf: f64,
    pub mmf: f64,
    pub cmf: f64,
}

/// Token information returned by GET /info.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LighterTokenInfo {
    pub token_id: u32,
    pub symbol: String,
    pub decimals: u32,
    pub mint_addr: String,
    pub weight_bps: u32,
}

/// Response from GET /info endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterInfoResponse {
    pub markets: Vec<LighterMarketInfo>,
    pub tokens: Vec<LighterTokenInfo>,
}

/// Orderbook entry (bid or ask).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterOrderbookLevel {
    pub price: String,
    pub size: String,
}

/// Response from GET /market/{id}/orderbook.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterOrderbookResponse {
    pub asks: Vec<LighterOrderbookLevel>,
    pub bids: Vec<LighterOrderbookLevel>,
    pub timestamp: u64,
    pub seq_num: u64,
}

/// A single trade from GET /trades.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterTrade {
    pub price: String,
    pub size: String,
    pub side: String,
    pub timestamp: u64,
}

/// Response from GET /trades.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterTradesResponse {
    pub trades: Vec<LighterTrade>,
}

/// Response from POST /action (transaction submission).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterActionResponse {
    pub action_id: Option<String>,
    pub status: Option<String>,
    pub tx_signature: Option<String>,
    pub id: Option<String>,
    pub client_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterOrderResponse {
    pub order_id: Option<u64>,
    pub order_index: Option<u64>,
    pub client_order_id: Option<u64>,
    pub client_order_index: Option<u64>,
    pub market_id: Option<u32>,
    pub market_index: Option<u32>,
    pub is_ask: Option<bool>,
    pub order_type: Option<String>,
    pub time_in_force: Option<String>,
    pub status: Option<String>,
    pub price: Option<String>,
    pub trigger_price: Option<String>,
    pub initial_base_amount: Option<String>,
    pub remaining_base_amount: Option<String>,
    pub filled_base_amount: Option<String>,
    pub average_price: Option<String>,
    pub timestamp: Option<u64>,
    pub updated_at: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterOrdersResponse {
    #[serde(default)]
    pub orders: Vec<LighterOrderResponse>,
    pub next: Option<String>,
    pub prev: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterFillResponse {
    pub id: Option<String>,
    pub trade_id: Option<String>,
    pub order_id: Option<u64>,
    pub order_index: Option<u64>,
    pub client_order_id: Option<u64>,
    pub client_order_index: Option<u64>,
    pub market_id: Option<u32>,
    pub market_index: Option<u32>,
    pub is_ask: Option<bool>,
    pub side: Option<String>,
    pub price: Option<String>,
    pub size: Option<String>,
    pub base_amount: Option<String>,
    pub quantity: Option<String>,
    pub liquidity: Option<String>,
    pub fee: Option<String>,
    pub fee_currency: Option<String>,
    pub timestamp: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterFillsResponse {
    #[serde(default)]
    pub trades: Vec<LighterFillResponse>,
    #[serde(default)]
    pub results: Vec<LighterFillResponse>,
    pub next: Option<String>,
    pub prev: Option<String>,
}
