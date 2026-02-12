use crate::websocket::messages::ApexOmniWsMessage;

/// Handler for incoming WebSocket messages from ApexOmni.
pub struct ApexOmniWsHandler;

impl ApexOmniWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<ApexOmniWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &ApexOmniWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
