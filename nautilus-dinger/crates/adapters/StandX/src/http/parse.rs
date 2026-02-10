use serde_json::Value;

pub fn parse_order_response(_response: Value) -> Result<String, String> {
    Ok("order_id".to_string())
}
