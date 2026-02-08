use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct {{EXCHANGE_NAME}}Config {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
}
