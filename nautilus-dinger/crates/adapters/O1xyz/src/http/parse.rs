use crate::common::models::{
    O1XyzInfoResponse,
    O1XyzOrderbookResponse,
    O1XyzTradesResponse,
};

/// Parse the /info response into market metadata.
pub fn parse_info_response(json: &str) -> Result<O1XyzInfoResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /market/{id}/orderbook response.
pub fn parse_orderbook_response(json: &str) -> Result<O1XyzOrderbookResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /trades response.
pub fn parse_trades_response(json: &str) -> Result<O1XyzTradesResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Extract market symbols from info response.
pub fn extract_symbols(info: &O1XyzInfoResponse) -> Vec<String> {
    info.markets.iter().map(|m| m.symbol.clone()).collect()
}
