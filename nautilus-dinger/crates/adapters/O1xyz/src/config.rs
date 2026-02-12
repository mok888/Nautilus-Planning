use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct O1XyzConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub ws_url: Option<String>,
    pub is_testnet: bool,
}

impl Default for O1XyzConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            api_secret: None,
            base_url: Some("https://zo-mainnet.n1.xyz".to_string()),
            ws_url: Some("wss://api.o1.exchange/ws".to_string()),
            is_testnet: false,
        }
    }
}

impl O1XyzConfig {
    pub fn get_base_url(&self) -> &str {
        if self.is_testnet {
            "https://zo-devnet.n1.xyz"
        } else {
            self.base_url
                .as_deref()
                .unwrap_or("https://zo-mainnet.n1.xyz")
        }
    }

    pub fn get_ws_url(&self) -> &str {
        self.ws_url
            .as_deref()
            .unwrap_or("wss://api.o1.exchange/ws")
    }
}
