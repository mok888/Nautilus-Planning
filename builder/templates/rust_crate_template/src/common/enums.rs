use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum {{EXCHANGE_NAME}}Side {
    Buy,
    Sell,
}
