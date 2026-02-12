use crate::common::models::{
    GrvtInfoResponse,
    GrvtOrderbookResponse,
    GrvtTradesResponse,
};

/// Parse the /info response into market metadata.
pub fn parse_info_response(json: &str) -> Result<GrvtInfoResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /market/{id}/orderbook response.
pub fn parse_orderbook_response(json: &str) -> Result<GrvtOrderbookResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /trades response.
pub fn parse_trades_response(json: &str) -> Result<GrvtTradesResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Extract market symbols from info response.
pub fn extract_symbols(info: &GrvtInfoResponse) -> Vec<String> {
    info.markets.iter().map(|m| m.symbol.clone()).collect()
}
