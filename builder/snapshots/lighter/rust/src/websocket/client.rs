/// WebSocket client for Lighter real-time data feeds.
///
/// Connects to `wss://mainnet.zklighter.elliot.ai/stream` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct LighterWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl LighterWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 30,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://mainnet.zklighter.elliot.ai/stream".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://mainnet.zklighter.elliot.ai/stream".to_string())
    }
}
