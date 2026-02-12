/// WebSocket client for 01.xyz real-time data feeds.
///
/// Connects to `wss://api.o1.exchange/ws` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct O1XyzWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl O1XyzWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 30,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://api.o1.exchange/ws".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://api.o1.exchange/ws".to_string())
    }
}
