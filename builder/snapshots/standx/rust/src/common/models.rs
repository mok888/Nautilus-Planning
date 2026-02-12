use serde::{Deserialize, Serialize};

/// A generic WebSocket or REST API message from StandX.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXMessage {
    pub id: String,
}

/// Market information returned by GET /info.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct StandXMarketInfo {
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
pub struct StandXTokenInfo {
    pub token_id: u32,
    pub symbol: String,
    pub decimals: u32,
    pub mint_addr: String,
    pub weight_bps: u32,
}

/// Response from GET /info endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXInfoResponse {
    pub markets: Vec<StandXMarketInfo>,
    pub tokens: Vec<StandXTokenInfo>,
}

/// Orderbook entry (bid or ask).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXOrderbookLevel {
    pub price: String,
    pub size: String,
}

/// Response from GET /market/{id}/orderbook.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXOrderbookResponse {
    pub asks: Vec<StandXOrderbookLevel>,
    pub bids: Vec<StandXOrderbookLevel>,
    pub timestamp: u64,
    pub seq_num: u64,
}

/// A single trade from GET /trades.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXTrade {
    pub price: String,
    pub size: String,
    pub side: String,
    pub timestamp: u64,
}

/// Response from GET /trades.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXTradesResponse {
    pub trades: Vec<StandXTrade>,
}

/// Response from POST /action (transaction submission).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXActionResponse {
    pub action_id: String,
    pub status: String,
    pub tx_signature: Option<String>,
}
