//! NautilusTrader Adapter - Lighter WebSocket Client

use crate::common::consts::WS_HEARTBEAT_INTERVAL_SEC;
use crate::config::LighterConfig;
use crate::error::{LighterError, Result};
use crate::http::signing::generate_signature;
use crate::parsing::models::WsResponse;
use futures_util::{SinkExt, StreamExt};
use serde_json::{json, Value};
use std::time::SystemTime;
use tokio::time::{interval, Duration};
use tokio_tungstenite::{connect_async, tungstenite::Message};

pub struct LighterWebSocketClient {
    config: LighterConfig,
}

impl LighterWebSocketClient {
    pub fn new(config: LighterConfig) -> Self {
        Self { config }
    }

    pub async fn connect_and_run<F>(
        &self,
        subscription_message: Value,
        mut callback: F,
    ) -> Result<()>
    where
        F: FnMut(WsResponse) + Send + 'static,
    {
        let url = "wss://api.lighter.xyz/ws";
        let (ws_stream, _) = connect_async(url)
            .await
            .map_err(|e| LighterError::WsError(e.to_string()))?;

        let (mut write, mut read) = ws_stream.split();

        // Authenticate if API key is present
        if let (Some(key), Some(secret)) = (&self.config.api_key, &self.config.api_secret) {
            let timestamp = SystemTime::now()
                .duration_since(SystemTime::UNIX_EPOCH)
                .unwrap()
                .as_millis() as u64;
            
            // Sign: timestamp + "CONNECT" + "/" + "" (based on standard auth flow, or empty payload)
            // Assuming auth requires a signed message payload.
            // Constructing a generic auth message struct based on DEX norms.
            let signature = generate_signature(&self.config, timestamp, "CONNECT", "/", "")?;
            
            let auth_msg = json!(
                {
                    "method": "AUTH",
                    "params": {
                        "apiKey": key,
                        "timestamp": timestamp,
                        "signature": signature,
                        "chainId": self.config.chain_id
                    }
                }
            );

            write
                .send(Message::Text(auth_msg.to_string()))
                .await
                .map_err(|e| LighterError::WsError(e.to_string()))?;
        }

        // Send initial subscription
        write
            .send(Message::Text(subscription_message.to_string()))
            .await
            .map_err(|e| LighterError::WsError(e.to_string()))?;

        // Heartbeat task
        let mut write_clone = write;
        let heartbeat_task = tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(WS_HEARTBEAT_INTERVAL_SEC));
            loop {
                interval.tick().await;
                // Standard ping frame
                if write_clone.send(Message::Ping(vec![])).await.is_err() {
                    break;
                }
            }
        });

        // Read loop
        while let Some(msg) = read.next().await {
            match msg {
                Ok(Message::Text(text)) => {
                    if let Ok(json_val) = serde_json::from_str::<Value>(&text) {
                        // Try to parse into known models
                        if let Ok(parsed) = serde_json::from_value::<WsResponse>(json_val.clone()) {
                            callback(parsed);
                        } else {
                            // Handle raw logs or unknown messages if necessary
                            log::debug!("Unknown WS message: {}", json_val);
                        }
                    }
                }
                Ok(Message::Pong(_)) => {
                    // Pong received, connection alive
                }
                Err(e) => {
                    log::error!("WS Error: {}", e);
                    break;
                }
                _ => {}
            }
        }

        heartbeat_task.abort();
        Ok(())
    }
}