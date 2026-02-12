use crate::websocket::messages::O1XyzWsMessage;

/// Handler for incoming WebSocket messages from 01.xyz.
pub struct O1XyzWsHandler;

impl O1XyzWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<O1XyzWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &O1XyzWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
