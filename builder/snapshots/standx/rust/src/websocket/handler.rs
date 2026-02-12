use crate::websocket::messages::StandXWsMessage;

/// Handler for incoming WebSocket messages from StandX.
pub struct StandXWsHandler;

impl StandXWsHandler {
    /// Process a raw JSON message from the WebSocket.
    pub fn handle_message(raw: &str) -> Result<StandXWsMessage, serde_json::Error> {
        serde_json::from_str(raw)
    }

    /// Check if the message is a heartbeat/pong.
    pub fn is_heartbeat(msg: &StandXWsMessage) -> bool {
        msg.msg_type.as_deref() == Some("pong")
    }
}
