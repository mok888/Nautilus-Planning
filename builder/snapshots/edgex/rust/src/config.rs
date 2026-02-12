use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EdgexConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for EdgexConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://pro.edgex.exchange".to_string()),
            ws_url: Some("wss://quote.edgex.exchange".to_string()),
            is_testnet: false,
        }
    }
}

impl EdgexConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://testnet.edgex.exchange"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://pro.edgex.exchange")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://quote.edgex.exchange")
    }
}
