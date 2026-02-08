// Copyright (C) 2024 Nautilus Technologies, Inc.
// SPDX-License-Identifier: MIT

use crate::config::LighterConfig;
use crate::error::{LighterAdapterError, Result};
use crate::http::signing::generate_headers;
use http::{header::CONTENT_TYPE, HeaderValue, Method, Request, Response, StatusCode, Uri};
use hyper::body::Body;
use nautilus_network::http::HttpClient;
use serde::{de::DeserializeOwned, Serialize};
use std::str::FromStr;

/// Concrete implementation of the Lighter REST API interaction.
pub struct LighterHttpClient {
    config: LighterConfig,
    base_url: String,
    client: HttpClient,
}

impl LighterHttpClient {
    pub fn new(config: LighterConfig) -> Result<Self> {
        let base_url = config
            .base_url
            .clone()
            .unwrap_or_else(|| LighterConfig::DEFAULT_BASE_URL.to_string());
        
        let client = HttpClient::new(nautilus_network::http::ClientConfig::default())
            .map_err(|e| LighterAdapterError::HttpClient(e.to_string()))?;

        Ok(Self {
            config,
            base_url,
            client,
        })
    }

    async fn request<R, S>(&self, method: Method, path: &str, body: Option<&S>, auth: bool) -> Result<R>
    where
        R: DeserializeOwned + Send + 'static,
        S: Serialize + Send + Sync,
    {
        let url_str = format!("{}{}", self.base_url, path);
        let uri = Uri::from_str(&url_str)
            .map_err(|e| LighterAdapterError::HttpClient(format!("Invalid URI: {}", e)))?;

        let body_bytes = match body {
            Some(b) => serde_json::to_vec(b)?,
            None => Vec::new(),
        };

        let mut request_builder = Request::builder()
            .method(method)
            .uri(uri);

        request_builder = request_builder.header(CONTENT_TYPE, HeaderValue::from_static("application/json"));

        // Add standard chain ID header for ALL requests as per schema notes
        request_builder = request_builder.header("x-lighter-chain-id", self.config.chain_id.as_str());

        if auth {
            let auth_headers = generate_headers(
                &self.config.api_key,
                &self.config.api_secret,
                &self.config.chain_id,
                method.as_str(),
                path,
                std::str::from_utf8(&body_bytes).unwrap_or(""),
            )?;
            // generate_headers returns x-lighter-chain-id again, but we handle duplicate headers gracefully or overwrite
            // We must ensure we don't double-add if generate_headers includes it, but here we rely on specific header list
            for (k, v) in auth_headers {
                request_builder = request_builder.header(k, v);
            }
        }

        let request = request_builder
            .body(Body::from(body_bytes))
            .map_err(|e| LighterAdapterError::HttpClient(format!("Failed to build request: {}", e)))?;

        let response = self
            .client
            .send(request)
            .await
            .map_err(|e| LighterAdapterError::HttpClient(e.to_string()))?;

        self.handle_response(response).await
    }

    async fn handle_response<R>(&self, response: Response<Body>) -> Result<R>
    where
        R: DeserializeOwned,
    {
        let status = response.status();
        let body_bytes = hyper::body::to_bytes(response.into_body())
            .await
            .map_err(|e| LighterAdapterError::HttpClient(format!("Failed to read response body: {}", e)))?;

        if status.is_success() {
            serde_json::from_slice(&body_bytes).map_err(Into::into)
        } else {
            let error_payload: serde_json::Value = serde_json::from_slice(&body_bytes).unwrap_or_default();
            let msg = error_payload["message"]
                .as_str()
                .or_else(|| error_payload["msg"].as_str())
                .unwrap_or_else(|| std::str::from_utf8(&body_bytes).unwrap_or("Unknown error"));
            let code = status.as_u16().to_string();
            Err(LighterAdapterError::Exchange { code, msg: msg.to_string() })
        }
    }
}

impl LighterHttpClient {
    /// Fetch tickers for the configured chain.
    /// Schema: GET /v1/tickers
    pub async fn get_tickers(&self) -> Result<Vec<serde_json::Value>> {
        // Note: x-lighter-chain-id is added automatically by request builder
        self.request(Method::GET, "/v1/tickers", None::<()>, false).await
    }

    /// Fetch orderbook for a symbol.
    /// Schema: GET /v1/orderbook?chainId=X&symbol=Y
    pub async fn get_orderbook(&self, symbol: &str) -> Result<serde_json::Value> {
        // We append query params manually. The chain ID is also sent via header as per requirement.
        let path = format!("/v1/orderbook?chainId={}&symbol={}", self.config.chain_id, symbol);
        self.request(Method::GET, &path, None::<()>, false).await
    }

    /// Create a new order.
    /// Schema: POST /v1/order
    pub async fn create_order(&self, order_payload: serde_json::Value) -> Result<serde_json::Value> {
        self.request(Method::POST, "/v1/order", Some(&order_payload), true).await
    }
}
