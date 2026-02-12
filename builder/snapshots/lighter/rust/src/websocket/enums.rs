use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LighterWsChannel {
    Orderbook,
    Trades,
    UserUpdates,
}

impl LighterWsChannel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Orderbook => "orderbook",
            Self::Trades => "trades",
            Self::UserUpdates => "user_updates",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LighterWsMessageType {
    Subscribe,
    Unsubscribe,
    Ping,
    Pong,
    Data,
    Error,
}
