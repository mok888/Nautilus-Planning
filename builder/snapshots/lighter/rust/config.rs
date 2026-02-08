//! NautilusTrader Adapter - Lighter Configuration

use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub chain_id: String,
    pub timeout_ms: u64,
}

impl Default for LighterConfig {
    fn default() -> Self {
        Self {
            api_key: env::var("Lighter_API_KEY").ok(),
            api_secret: env::var("Lighter_API_SECRET").ok(),
            chain_id: "137".to_string(), // Default to Polygon Mainnet
            timeout_ms: 5000,
        }
    }
}

impl LighterConfig {
    pub fn new(chain_id: String, api_key: String, api_secret: String) -> Self {
        Self {
            api_key: Some(api_key),
            api_secret: Some(api_secret),
            chain_id,
            ..Default::default()
        }
    }
}