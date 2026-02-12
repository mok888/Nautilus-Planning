use crate::common::models::{
    StandXInfoResponse,
    StandXOrderbookResponse,
    StandXTradesResponse,
};

/// Parse the /info response into market metadata.
pub fn parse_info_response(json: &str) -> Result<StandXInfoResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /market/{id}/orderbook response.
pub fn parse_orderbook_response(json: &str) -> Result<StandXOrderbookResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /trades response.
pub fn parse_trades_response(json: &str) -> Result<StandXTradesResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Extract market symbols from info response.
pub fn extract_symbols(info: &StandXInfoResponse) -> Vec<String> {
    info.markets.iter().map(|m| m.symbol.clone()).collect()
}
