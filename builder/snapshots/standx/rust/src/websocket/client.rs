/// WebSocket client for StandX real-time data feeds.
///
/// Connects to `wss://perps.standx.com/ws-stream/v1` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct StandXWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl StandXWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 30,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://perps.standx.com/ws-stream/v1".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://perps.standx.com/ws-stream/v1".to_string())
    }
}
