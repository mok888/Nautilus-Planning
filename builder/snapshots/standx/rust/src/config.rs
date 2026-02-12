use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for StandXConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://perps.standx.com".to_string()),
            ws_url: Some("wss://perps.standx.com/ws-stream/v1".to_string()),
            is_testnet: false,
        }
    }
}

impl StandXConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://testnet.perps.standx.com"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://perps.standx.com")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://perps.standx.com/ws-stream/v1")
    }
}
