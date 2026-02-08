//! NautilusTrader Adapter - Lighter URLs

/// Base URL for Lighter REST API
pub const REST_BASE_URL: &str = "https://api.lighter.xyz";

/// Base URL for Lighter WebSocket API
pub const WS_BASE_URL: &str = "wss://api.lighter.xyz/ws";

pub struct Endpoints;

impl Endpoints {
    pub fn tickers() -> String {
        format!("/{}{}", crate::common::consts::API_VERSION, "/tickers")
    }

    pub fn orderbook() -> String {
        format!("/{}{}", crate::common::consts::API_VERSION, "/orderbook")
    }

    pub fn order() -> String {
        format!("/{}{}", crate::common::consts::API_VERSION, "/order")
    }
}