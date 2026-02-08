use crate::config::LighterConfig;
use crate::error::{LighterError, Result};
use crate::http::signing::generate_signature;
use crate::parsing models::{OrderBook, OrderResponse, Ticker};

use hyper::body::{Bytes, Incoming};
use hyper::header::{AUTHORIZATION, CONTENT_TYPE};
use hyper::Request;
use hyper::{Method, StatusCode, Uri};
use hyper_util::client::legacy::connect::HttpConnector;
use hyper_util::client::legacy::Client;
use hyper_util::rt::TokioExecutor;
use http_body_util::{BodyExt, Full};
use hyper_rustls::HttpsConnector;
use governor::{
    clock::DefaultClock,
    state::{InMemoryState, NotKeyed},
    Quota, RateLimiter,
};
use serde::de::DeserializeOwned;
use std::num::NonZeroU32;
use std::sync::Arc;
use std::time::Duration;

pub struct HttpClient {
    config: LighterConfig,
    client: Client<HttpsConnector<HttpConnector>, Full<Bytes>>,
    rate_limiter: Arc<RateLimiter<NotKeyed, InMemoryState, DefaultClock>>,
}

impl HttpClient {
    pub fn new(config: LighterConfig) -> Self {
        let https = hyper_rustls::HttpsConnectorBuilder::new()
            .with_native_roots()
            .https_or_http()
            .enable_http1()
            .build();

        let client: Client<_, Full<Bytes>> = Client::builder(TokioExecutor::new()).build(https);

        // Rate limit: 120 requests per minute = 2 per second
        let quota = Quota::per_minute(NonZeroU32::new(120).unwrap());
        let rate_limiter = RateLimiter::direct(quota);

        Self {
            config,
            client,
            rate_limiter: Arc::new(rate_limiter),
        }
    }

    async fn request<B, R, O>(&self, method: Method, path: &str, body: B) -> Result<O>
    where
        B: serde::Serialize,
        O: DeserializeOwned,
    {
        // Rate limiting check (blocking for simplicity in this layer, non-blocking available via governor)
        self.rate_limiter.until_ready().await;

        let body_json = if method == Method::POST || method == Method::PUT {
            serde_json::to_string(&body)?
        } else {
            String::new()
        };

        let (timestamp, signature) = generate_signature(&self.config, method.as_str(), path, &body_json)?;

        let url_str = format!("{}{}", self.config.base_url, path);
        let uri: Uri = url_str.parse().map_err(|e| LighterError::Http(e.to_string()))?;

        let mut req_builder = Request::builder()
            .method(method)
            .uri(uri)
            .header("x-lighter-chain-id", &self.config.chain_id)
            .header("x-api-key", &self.config.api_key)
            .header("x-timestamp", timestamp)
            .header("x-signature", signature)
            .header(CONTENT_TYPE, "application/json");

        let req = if method == Method::POST || method == Method::PUT {
            req_builder
                .body(Full::new(Bytes::from(body_json)))
                .map_err(|e| LighterError::Http(e.to_string()))?
        } else {
            req_builder
                .body(Full::new(Bytes::new()))
                .map_err(|e| LighterError::Http(e.to_string()))?
        };

        let res = self.client.request(req).await?;

        if res.status() != StatusCode::OK {
            let status = res.status();
            let body_bytes = res.collect().await?.to_bytes();
            let err_str = String::from_utf8_lossy(&body_bytes).to_string();
            return Err(LighterError::Http(format!(
                "Status: {}, Body: {}",
                status, err_str
            )));
        }

        let body_bytes = res.collect().await?.to_bytes();
        let parsed: O = serde_json::from_slice(&body_bytes)?;
        Ok(parsed)
    }

    // --- Endpoints ---

    pub async fn get_tickers(&self) -> Result<Vec<Ticker>> {
        // Note: schema says request_fields: chainId. usually query param.
        // We assume chainId is handled in header for this specific API based on notes, 
        // but if query param needed, we append to path.
        self.request::<(), _, Vec<Ticker>>(Method::GET, "/v1/tickers", ()).await
    }

    pub async fn get_orderbook(&self, symbol: &str) -> Result<OrderBook> {
        // Placeholder for query param construction if needed by path logic
        let path = format!("/v1/orderbook?chainId={}&symbol={}", self.config.chain_id, symbol);
        self.request::<(), _, OrderBook>(Method::GET, &path, ()).await
    }

    pub async fn create_order(&self, order_req: crate::parsing::models::CreateOrderRequest) -> Result<OrderResponse> {
        self.request(Method::POST, "/v1/order", order_req).await
    }
}