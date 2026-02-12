use crate::websocket::messages::NadoWsMessage;

/// Handler for incoming WebSocket messages from Nado.
pub struct NadoWsHandler;

impl NadoWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<NadoWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &NadoWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
