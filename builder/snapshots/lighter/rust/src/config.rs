use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for LighterConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://mainnet.zklighter.elliot.ai".to_string()),
            ws_url: Some("wss://mainnet.zklighter.elliot.ai/stream".to_string()),
            is_testnet: false,
        }
    }
}

impl LighterConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://testnet.zklighter.elliot.ai"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://mainnet.zklighter.elliot.ai")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://mainnet.zklighter.elliot.ai/stream")
    }
}
