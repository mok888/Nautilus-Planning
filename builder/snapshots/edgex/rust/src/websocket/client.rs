/// WebSocket client for Edgex real-time data feeds.
///
/// Connects to `wss://quote.edgex.exchange` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct EdgexWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl EdgexWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 30,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://quote.edgex.exchange".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://quote.edgex.exchange".to_string())
    }
}
