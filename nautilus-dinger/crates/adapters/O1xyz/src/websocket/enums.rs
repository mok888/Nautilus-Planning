use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum O1XyzWsChannel {
    Orderbook,
    Trades,
    UserUpdates,
}

impl O1XyzWsChannel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Orderbook => "orderbook",
            Self::Trades => "trades",
            Self::UserUpdates => "user_updates",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum O1XyzWsMessageType {
    Subscribe,
    Unsubscribe,
    Ping,
    Pong,
    Data,
    Error,
}
