use serde_json::Value;

pub fn parse_ws_message(msg: &str) -> Result<Value, String> {
    serde_json::from_str(msg).map_err(|e| e.to_string())
}
