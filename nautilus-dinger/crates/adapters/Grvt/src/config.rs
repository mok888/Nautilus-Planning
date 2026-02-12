use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GrvtConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for GrvtConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://edge.grvt.io".to_string()),
            ws_url: Some("wss://trades.grvt.io/ws/full".to_string()),
            is_testnet: false,
        }
    }
}

impl GrvtConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://edge.testnet.grvt.io"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://edge.grvt.io")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://trades.grvt.io/ws/full")
    }
}
