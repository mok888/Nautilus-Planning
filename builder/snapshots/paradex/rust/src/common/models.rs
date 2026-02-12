use serde::{Deserialize, Serialize};

/// A generic WebSocket or REST API message from Paradex.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexMessage {
    pub id: String,
}

/// Market information returned by GET /info.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ParadexMarketInfo {
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
pub struct ParadexTokenInfo {
    pub token_id: u32,
    pub symbol: String,
    pub decimals: u32,
    pub mint_addr: String,
    pub weight_bps: u32,
}

/// Response from GET /info endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexInfoResponse {
    pub markets: Vec<ParadexMarketInfo>,
    pub tokens: Vec<ParadexTokenInfo>,
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
    pub timestamp: u64,
    pub seq_num: u64,
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
    pub action_id: String,
    pub status: String,
    pub tx_signature: Option<String>,
}
