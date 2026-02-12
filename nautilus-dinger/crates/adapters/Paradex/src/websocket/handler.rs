use crate::websocket::messages::ParadexWsMessage;

/// Handler for incoming WebSocket messages from Paradex.
pub struct ParadexWsHandler;

impl ParadexWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<ParadexWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &ParadexWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
