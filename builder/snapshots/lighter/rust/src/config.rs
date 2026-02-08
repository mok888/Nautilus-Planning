use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterConfig {
    pub api_key: String,
    pub secret_key: String,
    #[serde(default = "default_chain_id")]
    pub chain_id: String,
    #[serde(default = "default_base_url")]
    pub base_url: String,
    #[serde(default = "default_ws_url")]
    pub ws_url: String,
}

fn default_chain_id() -> String {
    "137".to_string() // Polygon Mainnet
}

fn default_base_url() -> String {
    "https://api.lighter.xyz".to_string()
}

fn default_ws_url() -> String {
    "wss://api.lighter.xyz/ws".to_string()
}