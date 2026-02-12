use serde::{Deserialize, Serialize};

/// Outbound WebSocket subscription message.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApexOmniWsSubscribe {
    pub op: String,
    pub channel: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub market: Option<String>,
}

impl ApexOmniWsSubscribe {
    pub fn subscribe(channel: &str, market: Option<&str>) -> Self {
        Self {
            op: "subscribe".to_string(),
            channel: channel.to_string(),
            market: market.map(|m| m.to_string()),
        }
    }

    pub fn unsubscribe(channel: &str, market: Option<&str>) -> Self {
        Self {
            op: "unsubscribe".to_string(),
            channel: channel.to_string(),
            market: market.map(|m| m.to_string()),
        }
    }
}

/// Inbound WebSocket message (generic envelope).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApexOmniWsMessage {
    #[serde(rename = "type")]
    pub msg_type: Option<String>,
    pub channel: Option<String>,
    pub data: Option<serde_json::Value>,
}

/// Heartbeat ping message.
#[derive(Debug, Clone, Serialize)]
pub struct ApexOmniWsPing {
    pub op: String,
}

impl Default for ApexOmniWsPing {
    fn default() -> Self {
        Self {
            op: "ping".to_string(),
        }
    }
}
