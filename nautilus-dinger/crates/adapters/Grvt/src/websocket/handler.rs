use crate::websocket::messages::GrvtWsMessage;

/// Handler for incoming WebSocket messages from Grvt.
pub struct GrvtWsHandler;

impl GrvtWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<GrvtWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &GrvtWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
