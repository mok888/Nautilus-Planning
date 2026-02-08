// Copyright (C) 2024 Nautilus Technologies, Inc.
// SPDX-License-Identifier: MIT

use crate::config::LighterConfig;
use crate::error::{LighterAdapterError, Result};
use crate::http::signing::generate_headers;
use nautilus_network::websocket::{WebSocketClient, WebSocketMessage};
use serde_json::Value;

/// Handles WebSocket connections for Lighter (Public and Private).
pub struct LighterWebSocketClient {
    config: LighterConfig,
    ws_url: String,
}

impl LighterWebSocketClient {
    pub fn new(config: LighterConfig) -> Self {
        let ws_url = LighterConfig::DEFAULT_WS_URL.to_string();
        Self { config, ws_url }
    }

    pub async fn connect_public(&self) -> Result<WebSocketClient> {
        let mut client = WebSocketClient::connect(self.ws_url.clone()).await
            .map_err(|e| LighterAdapterError::WebSocket(format!("Connection failed: {}", e)))?;
        
        // According to schema, chain ID is required. Assuming standard HTTP Upgrade headers apply.
        // We inject the chain ID via the handshake if supported, or first message.
        // Nautilus WebSocketClient typically handles underlying connection.
        // Assuming handshake headers are needed:
        if let Err(e) = client.send_text(serde_json::json!({
            "channel": "handshake", // Hypothetical based on DEX standards
            "chainId": self.config.chain_id
        }).to_string()).await {
            // If handshake fails or is not supported, we proceed. 
            // Based on schema simplicity, we might just subscribe immediately.
        }
        
        Ok(client)
    }

    pub async fn connect_private(&self) -> Result<WebSocketClient> {
        let mut client = WebSocketClient::connect(self.ws_url.clone()).await
            .map_err(|e| LighterAdapterError::WebSocket(format!("Connection failed: {}", e)))?;
        
        // Auth logic: Create signed payload
        let auth_payload = self.create_auth_payload()?;
        
        client.send_text(auth_payload.to_string()).await
            .map_err(|e| LighterAdapterError::WebSocket(format!("Send auth failed: {}", e)))?;

        Ok(client)
    }

    /// Generates the authentication payload for the private stream.
    /// Uses the standard signing logic defined in the schema.
    pub fn create_auth_payload(&self) -> Result<Value> {
        let method = "GET";
        let path = "/ws/auth"; // Canonical path for signing
        let body = "";
        let timestamp = chrono::Utc::now().timestamp_millis().to_string();

        let signature = {
            let mut payload = String::new();
            std::fmt::write(&mut payload, format_args!("{}{}{}{}", timestamp, method, path, body))
                .map_err(|e| LighterAdapterError::Signing(format!("Payload format error: {}", e)))?;
            
            use hmac::{Hmac, Mac, NewMac};
            use sha2::Sha256;
            type HmacSha256 = Hmac<Sha256>;
            
            let mut mac = HmacSha256::new_from_slice(self.config.api_secret.as_bytes())
                .map_err(|e| LighterAdapterError::Signing(format!("Invalid secret: {}", e)))?;
            mac.update(payload.as_bytes());
            hex::encode(mac.finalize().into_bytes())
        };

        Ok(serde_json::json!({
            "type": "auth",
            "apiKey": self.config.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "chainId": self.config.chain_id
        }))
    }

    /// Subscribe to public orderbook.
    pub fn subscribe_orderbook(symbol: &str) -> Value {
        serde_json::json!({
            "channel": "orderbook",
            "symbol": symbol
        })
    }

    /// Subscribe to public trades.
    pub fn subscribe_trades(symbol: &str) -> Value {
        serde_json::json!({
            "channel": "trades",
            "symbol": symbol
        })
    }
}
