/// WebSocket client for Grvt real-time data feeds.
///
/// Connects to `wss://trades.grvt.io/ws/full` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct GrvtWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl GrvtWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 10,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://trades.grvt.io/ws/full".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://trades.grvt.io/ws/full".to_string())
    }
}
