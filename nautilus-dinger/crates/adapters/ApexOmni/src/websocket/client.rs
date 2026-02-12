/// WebSocket client for ApexOmni real-time data feeds.
///
/// Connects to `wss://omni.apex.exchange/ws/v3` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct ApexOmniWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl ApexOmniWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 30,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://omni.apex.exchange/ws/v3".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://omni.apex.exchange/ws/v3".to_string())
    }
}
