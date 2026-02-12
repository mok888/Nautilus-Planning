use crate::websocket::messages::EdgexWsMessage;

/// Handler for incoming WebSocket messages from Edgex.
pub struct EdgexWsHandler;

impl EdgexWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<EdgexWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &EdgexWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
