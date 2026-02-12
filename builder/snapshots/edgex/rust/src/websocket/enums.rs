use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EdgexWsChannel {
    Orderbook,
    Trades,
    UserUpdates,
}

impl EdgexWsChannel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Orderbook => "orderbook",
            Self::Trades => "trades",
            Self::UserUpdates => "user_updates",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EdgexWsMessageType {
    Subscribe,
    Unsubscribe,
    Ping,
    Pong,
    Data,
    Error,
}
