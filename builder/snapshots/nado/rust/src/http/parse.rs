use crate::common::models::{
    NadoInfoResponse,
    NadoOrderbookResponse,
    NadoTradesResponse,
};

/// Parse the /info response into market metadata.
pub fn parse_info_response(json: &str) -> Result<NadoInfoResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /market/{id}/orderbook response.
pub fn parse_orderbook_response(json: &str) -> Result<NadoOrderbookResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Parse the /trades response.
pub fn parse_trades_response(json: &str) -> Result<NadoTradesResponse, serde_json::Error> {
    serde_json::from_str(json)
}

/// Extract market symbols from info response.
pub fn extract_symbols(info: &NadoInfoResponse) -> Vec<String> {
    info.markets.iter().map(|m| m.symbol.clone()).collect()
}
