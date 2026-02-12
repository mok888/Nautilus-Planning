use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApexOmniConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for ApexOmniConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://omni.apex.exchange/api".to_string()),
            ws_url: Some("wss://omni.apex.exchange/ws/v3".to_string()),
            is_testnet: false,
        }
    }
}

impl ApexOmniConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://omni.testnet.apex.exchange/api"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://omni.apex.exchange/api")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://omni.apex.exchange/ws/v3")
    }
}
