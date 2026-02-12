use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NadoConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for NadoConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://gateway.prod.nado.xyz".to_string()),
            ws_url: Some("wss://gateway.prod.nado.xyz/ws".to_string()),
            is_testnet: false,
        }
    }
}

impl NadoConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://gateway.testnet.nado.xyz"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://gateway.prod.nado.xyz")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://gateway.prod.nado.xyz/ws")
    }
}
