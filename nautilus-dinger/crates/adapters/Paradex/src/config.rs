use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for ParadexConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://api.prod.paradex.trade/v1".to_string()),
            ws_url: Some("wss://ws.api.prod.paradex.trade/v1".to_string()),
            is_testnet: false,
        }
    }
}

impl ParadexConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://api.testnet.paradex.trade/v1"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://api.prod.paradex.trade/v1")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://ws.api.prod.paradex.trade/v1")
    }
}
