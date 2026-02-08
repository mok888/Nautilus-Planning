// Copyright (C) 2024 Nautilus Technologies, Inc.
// SPDX-License-Identifier: MIT

use crate::error::Result;
use nautilus_model::data::order::{BookOrder, OrderSide};
use nautilus_model::identifiers::{instrument_id::InstrumentId, symbol::Symbol, venue::Venue};
use nautilus_model::types::{price::Price, quantity::Quantity};
use serde::{Deserialize, Deserializer};
use serde_json::Value;

/// Response from Get Tickers
#[derive(Debug, Deserialize)]
pub struct TickerResponse {
    pub symbol: String,
    #[serde(rename = "lastPrice")]
    pub last_price: String,
    pub volume: String,
    #[serde(rename = "priceStep")]
    pub price_step: String,
    #[serde(rename = "sizeStep")]
    pub size_step: String,
}

/// Response from Get Orderbook
#[derive(Debug, Deserialize)]
pub struct OrderbookResponse {
    pub asks: Vec<OrderBookLevel>,
    pub bids: Vec<OrderBookLevel>,
    pub timestamp: i64,
}

#[derive(Debug, Deserialize)]
pub struct OrderBookLevel {
    pub price: String,
    pub size: String,
}

/// Response from Create Order
#[derive(Debug, Deserialize)]
pub struct CreateOrderResponse {
    #[serde(rename = "orderId")]
    pub order_id: String,
    pub status: String,
    pub symbol: String,
}

// WebSocket Message Models

#[derive(Debug, Deserialize)]
#[serde(tag = "channel", content = "data")]
pub enum WsMessage {
    #[serde(rename = "orderbook")]
    Orderbook(OrderbookSnapshot),
    #[serde(rename = "trades")]
    Trades(TradeUpdate),
    #[serde(other)]
    Unknown,
}

#[derive(Debug, Deserialize)]
pub struct OrderbookSnapshot {
    pub symbol: String,
    pub asks: Vec<OrderBookLevel>,
    pub bids: Vec<OrderBookLevel>,
}

#[derive(Debug, Deserialize)]
pub struct TradeUpdate {
    pub symbol: String,
    pub trades: Vec<Trade>,
}

#[derive(Debug, Deserialize)]
pub struct Trade {
    pub price: String,
    pub size: String,
    pub side: String,
    pub timestamp: i64,
}

// Helper Parsing Functions

impl TickerResponse {
    pub fn parse_instrument_id(&self, venue: Venue) -> Result<InstrumentId> {
        let symbol = Symbol::new(&self.symbol)?;
        Ok(InstrumentId::new(symbol, venue))
    }
}

impl OrderBookLevel {
    pub fn to_book_order(&self, side: OrderSide) -> Result<BookOrder> {
        let price = Price::new(self.price.parse()?, 8)?;
        let size = Quantity::new(self.size.parse()?, 8)?;
        Ok(BookOrder::new(side, price, size, 0))
    }
}

impl Trade {
    pub fn parse_side(&self) -> Result<OrderSide> {
        match self.side.to_lowercase().as_str() {
            "buy" => Ok(OrderSide::Buy),
            "sell" => Ok(OrderSide::Sell),
            _ => Err(crate::error::LighterAdapterError::Parsing(format!("Invalid side: {}", self.side))),
        }
    }
}
