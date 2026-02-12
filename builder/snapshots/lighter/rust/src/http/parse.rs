use crate::common::models::{
    LighterInfoResponse,
    LighterOrderbookResponse,
    LighterTradesResponse,
};

/// Parse the /info response into market metadata.
pub fn parse_info_response(json: &str) -> Result<LighterInfoResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /market/{id}/orderbook response.
pub fn parse_orderbook_response(json: &str) -> Result<LighterOrderbookResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /trades response.
pub fn parse_trades_response(json: &str) -> Result<LighterTradesResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Extract market symbols from info response.
pub fn extract_symbols(info: &LighterInfoResponse) -> Vec<String> {
    info.markets.iter().map(|m| m.symbol.clone()).collect()
}
