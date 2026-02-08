use crate::config::LighterConfig;
use crate::error::{LighterError, Result};
use crate::http::signing::generate_signature;
use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use tokio_tungstenite::{connect_async, tungstenite::Message};

pub struct WebSocketClient {
    config: LighterConfig,
}

impl WebSocketClient {
    pub fn new(config: LighterConfig) -> Self {
        Self { config }
    }

    pub async fn connect_public(&self) -> Result<impl StreamExt<Item = Result<Message>>> {
        let url = format!("{}", self.config.ws_url);
        let (ws_stream, _) = connect_async(url).await?;
        Ok(ws_stream)
    }

    pub async fn connect_private(&self) -> Result<impl StreamExt<Item = Result<Message>>> {
        let url = format!("{}", self.config.ws_url);
        let (mut ws_stream, _) = connect_async(url).await?;

        // Auth Payload Construction
        // DEX WebSocket auth usually mirrors REST signature
        let path = "/ws"; // Virtual path for signing
        let body = "";
        let (timestamp, signature) = generate_signature(&self.config, "GET", path, body)?;

        let auth_msg = serde_json::json!({
            "method": "auth",
            "apiKey": self.config.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "chainId": self.config.chain_id
        });

        ws_stream
            .send(Message::Text(auth_msg.to_string()))
            .await?;

        Ok(ws_stream)
    }

    pub async fn subscribe_orderbook(&self, symbol: &str) -> Result<String> {
        Ok(serde_json::json!({
            "method": "subscribe",
            "channel": "orderbook",
            "symbol": symbol
        }).to_string())
    }
}