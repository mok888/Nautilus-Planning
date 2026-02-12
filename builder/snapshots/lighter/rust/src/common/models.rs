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
    pub action_id: String,
    pub status: String,
    pub tx_signature: Option<String>,
}
