use crate::websocket::messages::LighterWsMessage;

/// Handler for incoming WebSocket messages from Lighter.
pub struct LighterWsHandler;

impl LighterWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<LighterWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &LighterWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
