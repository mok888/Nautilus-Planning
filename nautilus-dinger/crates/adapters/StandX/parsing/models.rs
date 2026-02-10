use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct StandXResponse<T> {
    pub code: i32,
    pub message: Option<String>,
    #[serde(flatten)]
    pub data: Option<T>,
}

// Specific Models for Endpoints

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OrderResponse {
    pub request_id: String,
    // Add other fields as per actual response if necessary
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OrderInfo {
    pub id: String,
    pub symbol: String,
    pub side: String,
    pub order_type: String,
    pub status: String,
    pub price: String,
    pub qty: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BalanceResponse {
    pub isolated_balance: String,
    pub isolated_upnl: String,
    pub cross_balance: String,
    pub cross_margin: String,
    pub cross_upnl: String,
    pub locked: String,
    pub cross_available: String,
    pub balance: String,
    pub upnl: String,
    pub equity: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SymbolInfo {
    pub symbol: String,
    pub base_asset: String,
    pub quote_asset: String,
    pub price_tick_decimals: i32,
    pub qty_tick_decimals: i32,
    pub min_order_qty: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DepthBook {
    pub symbol: String,
    pub bids: Vec<Vec<String>>,
    pub asks: Vec<Vec<String>>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Trade {
    pub price: String,
    pub qty: String,
    pub side: String,
    pub time: i64,
}
