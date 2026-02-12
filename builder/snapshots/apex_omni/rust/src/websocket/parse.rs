use crate::websocket::messages::ApexOmniWsMessage;

/// Parse a raw WebSocket JSON payload into a typed message.
pub fn parse_ws_message(raw: &str) -> Result<ApexOmniWsMessage, serde_json::Error> {
    serde_json::from_str(raw)
}

/// Extract the channel name from a WebSocket message.
pub fn extract_channel(msg: &ApexOmniWsMessage) -> Option<&str> {
    msg.channel.as_deref()
}
