use crate::config::Credential;
use crate::error::{LighterAdapterError, Result};
use crate::http::signing::{generate_timestamp, Signer};
use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use tokio_tungstenite::tungstenite::protocol::Message;
use tokio_tungstenite::{connect_async, WebSocketStream};

type WsStream = WebSocketStream<tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>>;

pub struct WsClient {
    url: String,
    credential: Option<Credential>,
}

impl WsClient {
    pub fn new(url: String, credential: Option<Credential>) -> Self {
        Self { url, credential }
    }

    pub async fn connect(&self) -> Result<WsStream> {
        let url = url::Url::parse(&self.url)
            .map_err(|e| LighterAdapterError::AuthError(format!("Invalid WS URL: {}", e)))?;
        let (ws_stream, _) = connect_async(url).await?;
        Ok(ws_stream)
    }

    pub async fn authenticate(&self, ws_stream: &mut WsStream) -> Result<()> {
        if let Some(cred) = &self.credential {
            let timestamp = generate_timestamp();
            
            let signer = Signer::new(cred.api_secret.clone());
            // Standard WS signing path usually derived from the URL path
            let signature = signer.sign(timestamp, "GET", "/ws", "")?;

            let auth_payload = serde_json::json!({
                "type": "auth",
                "apiKey": cred.api_key,
                "timestamp": timestamp,
                "signature": signature
            });

            ws_stream.send(Message::Text(auth_payload.to_string())).await?;
            
            match ws_stream.next().await {
                Some(Ok(Message::Text(text))) => {
                    let json: Value = serde_json::from_str(&text)?;
                    if json["type"] == "auth" && json["success"] == true {
                        Ok(())
                    } else {
                        Err(LighterAdapterError::AuthError(format!("WS Auth failed: {}", text)))
                    }
                },
                Some(Ok(_)) => Err(LighterAdapterError::AuthError("Unexpected message type".to_string())),
                Some(Err(e)) => Err(LighterAdapterError::WebSocketClosed(e.to_string())),
                None => Err(LighterAdapterError::WebSocketClosed("Connection closed".to_string())),
            }
        } else {
            Ok(()) // Public mode
        }
    }
}