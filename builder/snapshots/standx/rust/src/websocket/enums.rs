use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StandXWsChannel {
    Orderbook,
    Trades,
    UserUpdates,
}

impl StandXWsChannel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Orderbook => "orderbook",
            Self::Trades => "trades",
            Self::UserUpdates => "user_updates",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StandXWsMessageType {
    Subscribe,
    Unsubscribe,
    Ping,
    Pong,
    Data,
    Error,
}
