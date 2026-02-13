use serde::{Deserialize, Serialize};
use serde_json::Value;

fn de_opt_string<'de, D>(deserializer: D) -> Result<Option<String>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let value = Option::<Value>::deserialize(deserializer)?;
    let out = match value {
        None | Some(Value::Null) => None,
        Some(Value::String(s)) => Some(s),
        Some(Value::Number(n)) => Some(n.to_string()),
        Some(Value::Bool(b)) => Some(b.to_string()),
        Some(other) => Some(other.to_string()),
    };
    Ok(out)
}

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
    #[serde(default)]
    pub action_id: String,
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub tx_signature: Option<String>,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub client_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXAccountStateResponse {
    #[serde(default, deserialize_with = "de_opt_string")]
    pub account_index: Option<String>,
    #[serde(default)]
    pub available_balance: Option<String>,
    #[serde(default)]
    pub collateral: Option<String>,
    #[serde(default)]
    pub total_asset_value: Option<String>,
    #[serde(default)]
    pub cross_asset_value: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub pending_order_count: Option<String>,
    #[serde(default)]
    pub positions: Vec<Value>,
    #[serde(default)]
    pub assets: Vec<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXOrderResponse {
    #[serde(default, deserialize_with = "de_opt_string")]
    pub id: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub order_id: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub order_index: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub client_id: Option<String>,
    #[serde(default, alias = "cl_ord_id", deserialize_with = "de_opt_string")]
    pub client_order_id: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub client_order_index: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub market: Option<String>,
    #[serde(default)]
    pub market_id: Option<u32>,
    #[serde(default)]
    pub market_index: Option<u32>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub symbol: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub side: Option<String>,
    #[serde(default)]
    pub is_ask: Option<bool>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub r#type: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub time_in_force: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub status: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub price: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub size: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub remaining_size: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub initial_base_amount: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub remaining_base_amount: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub filled_base_amount: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub trigger_price: Option<String>,
    #[serde(default)]
    pub reduce_only: Option<bool>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub avg_fill_price: Option<String>,
    #[serde(default)]
    pub timestamp: Option<Value>,
    #[serde(default)]
    pub created_at: Option<Value>,
    #[serde(default)]
    pub updated_at: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXOrdersResponse {
    #[serde(default)]
    pub orders: Vec<StandXOrderResponse>,
    #[serde(default)]
    pub result: Vec<StandXOrderResponse>,
    #[serde(default)]
    pub results: Vec<StandXOrderResponse>,
    #[serde(default)]
    pub next: Option<String>,
    #[serde(default)]
    pub prev: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXFillResponse {
    #[serde(default, deserialize_with = "de_opt_string")]
    pub id: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub trade_id: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub order_id: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub order_index: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub client_id: Option<String>,
    #[serde(default, alias = "cl_ord_id", deserialize_with = "de_opt_string")]
    pub client_order_id: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub client_order_index: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub market: Option<String>,
    #[serde(default)]
    pub market_id: Option<u32>,
    #[serde(default)]
    pub market_index: Option<u32>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub symbol: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub side: Option<String>,
    #[serde(default)]
    pub is_ask: Option<bool>,
    #[serde(default)]
    pub is_maker_ask: Option<bool>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub liquidity: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub price: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub size: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub base_amount: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub fee: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub maker_fee: Option<String>,
    #[serde(default, deserialize_with = "de_opt_string")]
    pub taker_fee: Option<String>,
    #[serde(default)]
    pub timestamp: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXFillsResponse {
    #[serde(default)]
    pub trades: Vec<StandXFillResponse>,
    #[serde(default)]
    pub result: Vec<StandXFillResponse>,
    #[serde(default)]
    pub results: Vec<StandXFillResponse>,
    #[serde(default)]
    pub next: Option<String>,
    #[serde(default)]
    pub prev: Option<String>,
}
