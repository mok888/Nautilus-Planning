use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub chain_id: String,
    #[serde(default = "default_base_url")]
    pub base_url: String,
    #[serde(default = "default_ws_url")]
    pub ws_url: String,
    pub timeout_ms: Option<u64>,
}

fn default_base_url() -> String {
    "https://api.lighter.xyz".to_string()
}

fn default_ws_url() -> String {
    "wss://api.lighter.xyz/ws".to_string()
}

#[derive(Debug, Clone)]
pub struct Credential {
    pub api_key: String,
    pub api_secret: String,
}

impl Credential {
    pub fn from_env() -> Option<Self> {
        let api_key = std::env::var("Lighter_API_KEY").ok()?;
        let api_secret = std::env::var("Lighter_API_SECRET").ok()?;
        Some(Self { api_key, api_secret })
    }
}