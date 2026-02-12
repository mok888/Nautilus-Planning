use crate::common::models::{
    ParadexInfoResponse,
    ParadexOrderbookResponse,
    ParadexTradesResponse,
};

/// Parse the /info response into market metadata.
pub fn parse_info_response(json: &str) -> Result<ParadexInfoResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /market/{id}/orderbook response.
pub fn parse_orderbook_response(json: &str) -> Result<ParadexOrderbookResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /trades response.
pub fn parse_trades_response(json: &str) -> Result<ParadexTradesResponse, serde_json::Error> {
    serde_json::from_str(json)
}

pub fn extract_symbols(info: &ParadexInfoResponse) -> Vec<String> {
    info.results.iter().map(|m| m.symbol.clone()).collect()
}
