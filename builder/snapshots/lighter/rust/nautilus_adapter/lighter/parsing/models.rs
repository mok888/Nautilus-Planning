use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
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

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OrderbookLevel {
    pub price: String,
    pub quantity: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Orderbook {
    pub asks: Vec<OrderbookLevel>,
    pub bids: Vec<OrderbookLevel>,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct LighterOrder {
    #[serde(rename = "orderId")]
    pub order_id: String,
    pub status: String,
    pub symbol: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct WsMessage {
    #[serde(rename = "type")]
    pub msg_type: String,
    pub data: Value,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Trade {
    pub id: String,
    pub price: String,
    pub quantity: String,
    pub side: String,
    pub timestamp: i64,
}