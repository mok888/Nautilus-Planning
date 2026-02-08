use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct {{EXCHANGE_NAME}}Message {
    pub id: String,
}
