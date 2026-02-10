use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
}
