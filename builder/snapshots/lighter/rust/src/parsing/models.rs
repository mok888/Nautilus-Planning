use serde::{Deserialize, Serialize};

// --- Tickers ---

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

// --- Orderbook ---

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OrderBook {
    pub asks: Vec<[String; 2]>, // [price, size]
    pub bids: Vec<[String; 2]>, // [price, size]
    pub timestamp: u64,
}

// --- Order ---

#[derive(Debug, Clone, Serialize)]
pub struct CreateOrderRequest {
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
    pub tif: String, // Time in Force, e.g., "GTC"
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OrderResponse {
    #[serde(rename = "orderId")]
    pub order_id: String,
    pub status: String,
    pub symbol: String,
}