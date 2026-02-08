//! NautilusTrader Adapter - Lighter Models

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ticker {
    pub symbol: String,
    #[serde(rename = "lastPrice")]
    pub last_price: String,
    pub volume: String,
    #[serde(rename = "priceStep")]
    pub price_step: String,
    #[serde(rename = "sizeStep")]
    pub size_step: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBookLevel {
    pub price: String,
    pub quantity: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBook {
    pub asks: Vec<OrderBookLevel>,
    pub bids: Vec<OrderBookLevel>,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct OrderRequest {
    #[serde(rename = "chainId")]
    pub chain_id: String,
    pub symbol: String,
    pub side: String, // "BUY" or "SELL"
    #[serde(rename = "type")]
    pub order_type: String, // "LIMIT" or "MARKET"
    pub price: String,
    pub quantity: String,
    #[serde(rename = "clientOrderId")]
    pub client_order_id: String,
    #[serde(rename = "tif")]
    pub time_in_force: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderResponse {
    #[serde(rename = "orderId")]
    pub order_id: String,
    pub status: String,
    pub symbol: String,
}

// WebSocket Messages

#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "channel", content = "data")]
pub enum WsResponse {
    #[serde(rename = "orderbook")]
    OrderBook(OrderBook),
    #[serde(rename = "trades")]
    Trades(Vec<Trade>),
    #[serde(rename = "orderUpdate")]
    OrderUpdate(OrderUpdate),
    #[serde(rename = "account")]
    Account(AccountUpdate),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub id: String,
    pub price: String,
    pub quantity: String,
    pub side: String,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderUpdate {
    #[serde(rename = "orderId")]
    pub order_id: String,
    pub symbol: String,
    pub status: String,
    pub price: String,
    pub filled_qty: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountUpdate {
    pub balances: Vec<Balance>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Balance {
    pub asset: String,
    pub free: String,
    pub locked: String,
}
