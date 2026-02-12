/// WebSocket client for Nado real-time data feeds.
///
/// Connects to `wss://gateway.prod.nado.xyz/ws` for both public and private channels.
/// Public channels: orderbook, trades
/// Private channels: user_updates (requires authentication)
pub struct NadoWebSocketClient {
    pub url: String,
    pub heartbeat_interval_secs: u64,
}

impl NadoWebSocketClient {
    pub fn new(url: String) -> Self {
        Self {
            url,
            heartbeat_interval_secs: 30,
        }
    }

    pub fn new_public() -> Self {
        Self::new("wss://gateway.prod.nado.xyz/ws".to_string())
    }

    pub fn new_private() -> Self {
        Self::new("wss://gateway.prod.nado.xyz/ws".to_string())
    }
}
