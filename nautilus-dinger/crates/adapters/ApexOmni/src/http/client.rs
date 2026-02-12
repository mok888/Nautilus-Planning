use std::sync::Arc;
use nautilus_network::http::HttpClient;
use nautilus_common::live::get_runtime;

use crate::common::credential::ApexOmniCredential;
use crate::common::models::{
    ApexOmniInfoResponse,
    ApexOmniOrderbookResponse,
    ApexOmniTradesResponse,
    ApexOmniActionResponse,
};

/// Raw HTTP client matching ApexOmni venue API endpoints.
pub struct ApexOmniRawHttpClient {
    base_url: String,
    client: HttpClient,
    credential: Option<ApexOmniCredential>,
}

/// Domain HTTP client exposing Nautilus types.
pub struct ApexOmniHttpClient {
    inner: Arc<ApexOmniRawHttpClient>,
}

impl ApexOmniHttpClient {
    pub fn new(
        base_url: String,
        client: HttpClient,
        credential: Option<ApexOmniCredential>,
    ) -> Self {
        Self {
            inner: Arc::new(ApexOmniRawHttpClient {
                base_url,
                client,
                credential,
            }),
        }
    }

    /// Fetch exchange info including markets and tokens.
    /// GET /info
    pub fn get_info(&self) -> anyhow::Result<ApexOmniInfoResponse> {
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            let url = format!("{}/info", inner.base_url);
            let response = inner.client.get(url, None, None, None, None).await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let info: ApexOmniInfoResponse = serde_json::from_slice(&response.body)?;
            Ok(info)
        })
    }

    /// Fetch orderbook for a given market.
    /// GET /market/{market_id}/orderbook
    pub fn get_orderbook(&self, market_id: u32) -> anyhow::Result<ApexOmniOrderbookResponse> {
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            let url = format!("{}/market/{}/orderbook", inner.base_url, market_id);
            let response = inner.client.get(url, None, None, None, None).await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let orderbook: ApexOmniOrderbookResponse = serde_json::from_slice(&response.body)?;
            Ok(orderbook)
        })
    }

    /// Fetch recent trades.
    /// GET /trades
    pub fn get_trades(
        &self,
        market_id: u32,
        limit: Option<u32>,
    ) -> anyhow::Result<ApexOmniTradesResponse> {
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            let mut url = format!("{}/trades?market_id={}", inner.base_url, market_id);
            if let Some(limit) = limit {
                url.push_str(&format!("&limit={}", limit));
            }
            let response = inner.client.get(url, None, None, None, None).await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let trades: ApexOmniTradesResponse = serde_json::from_slice(&response.body)?;
            Ok(trades)
        })
    }

    /// Get server timestamp.
    /// GET /timestamp
    pub fn get_timestamp(&self) -> anyhow::Result<u64> {
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            let url = format!("{}/timestamp", inner.base_url);
            let response = inner.client.get(url, None, None, None, None).await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let body_str = std::str::from_utf8(&response.body)?;
            let ts: u64 = body_str.trim().parse()?;
            Ok(ts)
        })
    }

    /// Submit a transaction action (place/cancel order).
    /// POST /action
    pub fn submit_action(&self, payload: &str) -> anyhow::Result<ApexOmniActionResponse> {
        let inner = self.inner.clone();
        let body_bytes = payload.as_bytes().to_vec();
        get_runtime().block_on(async move {
            let url = format!("{}/action", inner.base_url);
            let response = inner.client.post(url, None, None, Some(body_bytes), None, None).await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let action: ApexOmniActionResponse = serde_json::from_slice(&response.body)?;
            Ok(action)
        })
    }
}
