use serde::{Deserialize, Serialize};

/// Generic HTTP request payload for POST /action.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterActionRequest {
    pub action: String,
    pub account_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub market_id: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub price: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub size: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub side: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub order_type: Option<String>,
}

/// HTTP response wrapper used for error reporting.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterHttpErrorResponse {
    pub error: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

/// Market stats returned by GET /market/{id}/stats.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterMarketStats {
    pub price: String,
    pub volume: String,
    pub mark_price: String,
    pub index_price: String,
    pub funding_rate: String,
    pub open_interest: String,
    pub funding_interval: Option<String>,
}
