//! NautilusTrader Adapter - Lighter HTTP Client

use crate::common::consts::{
    HEADER_API_KEY, HEADER_CHAIN_ID, HEADER_SIGNATURE, HEADER_TIMESTAMP, RATE_LIMIT_LIMIT,
    RATE_LIMIT_PERIOD_MS,
};
use crate::common::urls::REST_BASE_URL;
use crate::config::LighterConfig;
use crate::error::{LighterError, Result};
use crate::http::signing::generate_signature;
use governor::{
    clock::DefaultClock, state::InMemoryState, Quota, RateLimiter,
};
use hyper::body::{Body, Incoming};
use hyper::http::HeaderMap;
use hyper::Request;
use hyper_rustls::HttpsConnectorBuilder;
use hyper_util::{
    client::legacy::{connect::HttpConnector, Client},
    rt::TokioExecutor,
};
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub struct LighterHttpClient {
    config: LighterConfig,
    client: Client<HttpsConnector<HttpConnector>, Body>,
    rate_limiter: Arc<RateLimiter<InMemoryState, DefaultClock>>,
}

impl LighterHttpClient {
    pub fn new(config: LighterConfig) -> Self {
        let https = HttpsConnectorBuilder::new()
            .with_native_roots()
            .unwrap()
            .https_or_http()
            .enable_http1()
            .build();

        let client: Client<_, Body> = Client::builder(TokioExecutor::new()).build(https);

        // Rate Limit: 120 requests per 1 minute
        let quota = Quota::per_minute(RATE_LIMIT_LIMIT);
        let rate_limiter = RateLimiter::direct(quota);

        Self {
            config,
            client,
            rate_limiter: Arc::new(rate_limiter),
        }
    }

    async fn request_inner<B>(&self, method: hyper::Method, path: &str, body: B) -> Result<String>
    where
        B: hyper::body::Body + Send + 'static,
        B::Data: Send,
        B::Error: Into<Box<dyn std::error::Error + Send + Sync>>,
    {
        // Rate limiting check
        self.rate_limiter
            .until_ready()
            .await;

        let full_url = format!("{}{}", REST_BASE_URL, path);

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        // Determine body string for signing
        let body_bytes = match std::mem::replace(&mut body.into_eof(), true) {
            true => String::new(), // Hacky check, normally we'd buffer. For Lighter GET body is empty.
            false => {
                // Since we can't easily extract generic Body bytes without consuming,
                // we assume GET/DELETE empty, POST/PUT known.
                // We will pass explicit string to helper methods.
                String::new()
            }
        };

        // Since hyper body consumption is tricky before sending, we restructure request building
        // to expect explicit body string for signing logic separation.
        // This method is generic, but signing needs the body content.
        // We'll implement specific verbs to handle this cleanly.
        Err(LighterError::ConfigError(
            "Use specific methods (get/post)".to_string(),
        ))
    }

    pub async fn get(&self, path: &str, query: Option<&str>) -> Result<String> {
        let req_path = if let Some(q) = query {
            format!("{}?{}", path, q)
        } else {
            path.to_string()
        };
        self.execute("GET", &req_path, "").await
    }

    pub async fn post(&self, path: &str, body_json: &str) -> Result<String> {
        self.execute("POST", path, body_json).await
    }

    async fn execute(&self, method: &str, path: &str, body_str: &str) -> Result<String> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        let signature = generate_signature(&self.config, timestamp, method, path, body_str)?;

        let full_uri = format!("{}{}", REST_BASE_URL, path);
        let uri = full_uri.parse().map_err(|e| LighterError::ConfigError(format!("Invalid URI: {}", e)))?;

        let mut req_builder = Request::builder()
            .method(method)
            .uri(uri)
            .header("content-type", "application/json")
            .header(HEADER_CHAIN_ID, &self.config.chain_id)
            .header(HEADER_TIMESTAMP, timestamp.to_string())
            .header(HEADER_SIGNATURE, signature);

        if let Some(api_key) = &self.config.api_key {
            req_builder = req_builder.header(HEADER_API_KEY, api_key);
        }

        let req = if body_str.is_empty() {
            req_builder.body(Body::empty())?
        } else {
            req_builder.body(Body::from(body_str.to_owned()))?
        };

        let mut resp = self.client.request(req).await?;

        let status = resp.status();
        let body_bytes = hyper::body::collect(resp.into_body())
            .await?
            .to_bytes();

        let response_str = String::from_utf8(body_bytes.to_vec())
            .map_err(|e| LighterError::JsonError(serde_json::Error::custom(e)))?;

        if !status.is_success() {
            // Attempt to parse API error
            if let Ok(api_err) = serde_json::from_str::<serde_json::Value>(&response_str) {
                return Err(LighterError::ApiError {
                    code: status.as_u16() as i32,
                    message: api_err["message"].as_str().unwrap_or("Unknown error").to_string(),
                });
            }
            return Err(LighterError::HttpError(hyper::Error::new(
                format!("HTTP {} error: {}", status, response_str).as_str(),
            )));
        }

        Ok(response_str)
    }
}