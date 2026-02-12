/// WebSocket client for Paradex real-time data feeds.
///
/// Connects to `wss://ws.api.prod.paradex.trade/v1` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct ParadexWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl ParadexWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 30,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://ws.api.prod.paradex.trade/v1".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://ws.api.prod.paradex.trade/v1".to_string())
    }
}
