use crate::config::StandXConfig;
use crate::error::StandXError;
use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use tokio_tungstenite::{connect_async, tungstenite::Message};
use tracing::{info, error};

pub struct StandXWebSocketClient {
    config: StandXConfig,
}

impl StandXWebSocketClient {
    pub fn new(config: StandXConfig) -> Self {
        Self { config }
    }

    pub async fn connect_public(&self, symbol: &str, channels: Vec<String>) -> Result<(), StandXError> {
        let url = self.config.get_ws_public_url();
        info!("Connecting to StandX Public WS: {}", url);

        let (ws_stream, _) = connect_async(&url)
            .await
            .map_err(|e| StandXError::WsError(e.to_string()))?;

        let (mut write, mut read) = ws_stream.split();

        // Subscribe to channels
        for channel in channels {
            let payload = serde_json::json!({
                "channel": channel,
                "symbol": symbol,
                "event": "subscribe"
            });
            
            let msg = Message::Text(payload.to_string());
            write.send(msg).await.map_err(|e| StandXError::WsError(e.to_string()))?;
            info!("Subscribed to {} for {}", channel, symbol);
        }

        // Read loop
        while let Some(msg) = read.next().await {
            match msg {
                Ok(Message::Text(text)) => {
                    if let Ok(v) = serde_json::from_str::<Value>(&text) {
                        self.handle_public_message(v);
                    }
                }
                Ok(Message::Close(_)) => {
                    info!("WS Close received");
                    break;
                }
                Err(e) => {
                    error!("WS Error: {}", e);
                    return Err(StandXError::WsError(e.to_string()));
                }
                _ => {}
            }
        }

        Ok(())
    }

    fn handle_public_message(&self, data: Value) {
        // Dispatch data to Nautilus core
        // Placeholder for parsing logic: price_book, trade, etc.
        info!("Received Public WS Message: {}", data);
    }
}
