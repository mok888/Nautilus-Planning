use http::Method;
use nautilus_common::live::get_runtime;
use nautilus_network::http::HttpClient;
use serde_json::json;
use std::collections::HashMap;
use std::sync::Arc;

use crate::common::credential::LighterCredential;
use crate::common::models::{
    LighterActionResponse, LighterFillResponse, LighterFillsResponse, LighterInfoResponse,
    LighterOrderResponse, LighterOrderbookResponse, LighterOrdersResponse, LighterTradesResponse,
};

/// Raw HTTP client matching Lighter venue API endpoints.
pub struct LighterRawHttpClient {
    base_url: String,
    client: HttpClient,
    credential: Option<LighterCredential>,
}

impl LighterRawHttpClient {
    pub fn new(
        base_url: String,
        client: HttpClient,
        credential: Option<LighterCredential>,
    ) -> Self {
        Self { base_url, client, credential }
    }

    pub fn base_url(&self) -> &str {
        &self.base_url
    }

    /// Fetch exchange info including markets and tokens.
    /// GET /info
    pub fn get_info(&self) -> anyhow::Result<LighterInfoResponse> {
        get_runtime().block_on(async {
            let url = format!("{}/info", self.base_url);
            let response = self
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let info: LighterInfoResponse = serde_json::from_slice(&response.body)?;
            Ok(info)
        })
    }

    /// Fetch orderbook for a given market.
    /// GET /market/{market_id}/orderbook
    pub fn get_orderbook(&self, market_id: u32) -> anyhow::Result<LighterOrderbookResponse> {
        get_runtime().block_on(async {
            let url = format!("{}/market/{}/orderbook", self.base_url, market_id);
            let response = self
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let orderbook: LighterOrderbookResponse = serde_json::from_slice(&response.body)?;
            Ok(orderbook)
        })
    }

    /// Fetch recent trades.
    /// GET /trades
    pub fn get_trades(
        &self,
        market_id: u32,
        limit: Option<u32>,
    ) -> anyhow::Result<LighterTradesResponse> {
        get_runtime().block_on(async {
            let mut url = format!("{}/trades?market_id={}", self.base_url, market_id);
            if let Some(limit) = limit {
                url.push_str(&format!("&limit={}", limit));
            }
            let response = self
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let trades: LighterTradesResponse = serde_json::from_slice(&response.body)?;
            Ok(trades)
        })
    }

    /// Get server timestamp.
    /// GET /timestamp
    pub fn get_timestamp(&self) -> anyhow::Result<u64> {
        get_runtime().block_on(async {
            let url = format!("{}/timestamp", self.base_url);
            let response = self
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let body_str = std::str::from_utf8(&response.body)?;
            let ts: u64 = body_str.trim().parse()?;
            Ok(ts)
        })
    }

    /// Submit a transaction action (place/cancel order).
    /// POST /action
    pub fn submit_action(&self, payload: &str) -> anyhow::Result<LighterActionResponse> {
        let body_bytes = payload.as_bytes().to_vec();
        get_runtime().block_on(async {
            let url = format!("{}/action", self.base_url);
            let response = self
                .client
                .post(url, None, None, Some(body_bytes), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let action: LighterActionResponse = serde_json::from_slice(&response.body)?;
            Ok(action)
        })
    }
}

/// Domain HTTP client exposing Nautilus types.
pub struct LighterHttpClient {
    inner: Arc<LighterRawHttpClient>,
}

impl LighterHttpClient {
    pub fn new(
        base_url: String,
        client: HttpClient,
        credential: Option<LighterCredential>,
    ) -> Self {
        Self { inner: Arc::new(LighterRawHttpClient::new(base_url, client, credential)) }
    }

    /// Fetch exchange info including markets and tokens.
    /// GET /info
    pub fn get_info(&self) -> anyhow::Result<LighterInfoResponse> {
        self.inner.get_info()
    }

    /// Fetch orderbook for a given market.
    /// GET /market/{market_id}/orderbook
    pub fn get_orderbook(&self, market_id: u32) -> anyhow::Result<LighterOrderbookResponse> {
        self.inner.get_orderbook(market_id)
    }

    /// Fetch recent trades.
    /// GET /trades
    pub fn get_trades(
        &self,
        market_id: u32,
        limit: Option<u32>,
    ) -> anyhow::Result<LighterTradesResponse> {
        self.inner.get_trades(market_id, limit)
    }

    /// Get server timestamp.
    /// GET /timestamp
    pub fn get_timestamp(&self) -> anyhow::Result<u64> {
        self.inner.get_timestamp()
    }

    /// Submit a transaction action (place/cancel order).
    /// POST /action
    pub fn submit_action(&self, payload: &str) -> anyhow::Result<LighterActionResponse> {
        self.inner.submit_action(payload)
    }

    fn auth_headers(&self) -> anyhow::Result<HashMap<String, String>> {
        let creds = self
            .inner
            .credential
            .as_ref()
            .ok_or_else(|| anyhow::anyhow!("No credentials configured"))?;

        let mut headers = HashMap::new();
        headers.insert("Authorization".to_string(), creds.authorization_header());
        Ok(headers)
    }

    #[allow(clippy::too_many_arguments)]
    pub fn submit_order(
        &self,
        market: String,
        side: String,
        order_type: String,
        size: String,
        price: String,
        client_id: Option<String>,
        instruction: Option<String>,
        trigger_price: Option<String>,
        reduce_only: bool,
        signature_timestamp_ms: Option<u64>,
    ) -> anyhow::Result<LighterActionResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/v1/order", inner.base_url);
            let payload = json!({
                "market": market,
                "side": side,
                "type": order_type,
                "size": size,
                "price": price,
                "client_order_id": client_id,
                "instruction": instruction,
                "trigger_price": trigger_price,
                "reduce_only": reduce_only,
                "signature_timestamp_ms": signature_timestamp_ms,
            });

            let response = inner
                .client
                .request(
                    Method::POST,
                    url,
                    None,
                    Some(headers),
                    Some(serde_json::to_vec(&payload)?),
                    None,
                    None,
                )
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Order submit failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let value: serde_json::Value = serde_json::from_slice(&response.body)?;
            Ok(LighterActionResponse {
                action_id: value.get("action_id").and_then(|v| v.as_str()).map(str::to_string),
                status: value.get("status").and_then(|v| v.as_str()).map(str::to_string),
                tx_signature: value
                    .get("tx_signature")
                    .and_then(|v| v.as_str())
                    .map(str::to_string),
                id: value
                    .get("id")
                    .or_else(|| value.get("tx_hash"))
                    .and_then(|v| v.as_str())
                    .map(str::to_string),
                client_id: value
                    .get("client_order_id")
                    .or_else(|| value.get("client_id"))
                    .and_then(|v| v.as_str())
                    .map(str::to_string),
            })
        })
    }

    pub fn cancel_order_by_client_id(
        &self,
        client_id: String,
        market: Option<String>,
    ) -> anyhow::Result<()> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/v1/order/by-client-id/{}", inner.base_url, client_id);
            let payload =
                if let Some(market) = market { Some(json!({ "market": market })) } else { None };

            let response = inner
                .client
                .request(
                    Method::DELETE,
                    url,
                    None,
                    Some(headers),
                    payload.map(|p| serde_json::to_vec(&p)).transpose()?,
                    None,
                    None,
                )
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Cancel by client id failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            Ok(())
        })
    }

    pub fn cancel_order(&self, order_id: String) -> anyhow::Result<()> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/v1/order/{}", inner.base_url, order_id);
            let response = inner
                .client
                .request(Method::DELETE, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!("Cancel failed {:?}: {}", response.status, body_text));
            }

            Ok(())
        })
    }

    pub fn cancel_all_orders(&self, market: Option<String>) -> anyhow::Result<()> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let mut url = format!("{}/api/v1/order", inner.base_url);
            if let Some(market) = market {
                url.push_str(&format!("?market={market}"));
            }

            let response = inner
                .client
                .request(Method::DELETE, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Cancel all failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            Ok(())
        })
    }

    #[allow(clippy::too_many_arguments)]
    pub fn modify_order(
        &self,
        order_id: String,
        market: String,
        side: String,
        order_type: String,
        size: String,
        price: String,
        trigger_price: Option<String>,
        signature_timestamp_ms: Option<u64>,
    ) -> anyhow::Result<LighterOrderResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/v1/order/{}", inner.base_url, order_id);
            let payload = json!({
                "market": market,
                "side": side,
                "type": order_type,
                "size": size,
                "price": price,
                "trigger_price": trigger_price,
                "signature_timestamp_ms": signature_timestamp_ms,
            });

            let response = inner
                .client
                .request(
                    Method::PUT,
                    url,
                    None,
                    Some(headers),
                    Some(serde_json::to_vec(&payload)?),
                    None,
                    None,
                )
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Modify order failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let order: LighterOrderResponse = serde_json::from_slice(&response.body)?;
            Ok(order)
        })
    }

    pub fn get_open_orders(
        &self,
        market: Option<String>,
    ) -> anyhow::Result<Vec<LighterOrderResponse>> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let mut url = format!("{}/api/v1/accountActiveOrders", inner.base_url);
            if let Some(market) = market {
                url.push_str(&format!("?market={market}"));
            }

            let response = inner
                .client
                .request(Method::GET, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Get open orders failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let wrapper: LighterOrdersResponse = match serde_json::from_slice(&response.body) {
                Ok(parsed) => parsed,
                Err(_) => {
                    let rows: Vec<LighterOrderResponse> = serde_json::from_slice(&response.body)?;
                    LighterOrdersResponse { orders: rows, next: None, prev: None }
                }
            };
            Ok(wrapper.orders)
        })
    }

    pub fn get_order_by_id(&self, order_id: String) -> anyhow::Result<LighterOrderResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/v1/order/{}", inner.base_url, order_id);
            let response = inner
                .client
                .request(Method::GET, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Get order by id failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let order: LighterOrderResponse = serde_json::from_slice(&response.body)?;
            Ok(order)
        })
    }

    pub fn get_order_by_client_id(
        &self,
        client_id: String,
    ) -> anyhow::Result<LighterOrderResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/v1/order/by-client-id/{}", inner.base_url, client_id);
            let response = inner
                .client
                .request(Method::GET, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Get order by client id failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let order: LighterOrderResponse = serde_json::from_slice(&response.body)?;
            Ok(order)
        })
    }

    pub fn get_orders_history(
        &self,
        market: Option<String>,
        client_id: Option<String>,
        start_at_ms: Option<u64>,
        end_at_ms: Option<u64>,
        page_size: Option<u32>,
    ) -> anyhow::Result<LighterOrdersResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let mut params = vec![];
            if let Some(market) = market {
                params.push(("market", market));
            }
            if let Some(client_id) = client_id {
                params.push(("client_id", client_id));
            }
            if let Some(start_at_ms) = start_at_ms {
                params.push(("start_at_ms", start_at_ms.to_string()));
            }
            if let Some(end_at_ms) = end_at_ms {
                params.push(("end_at_ms", end_at_ms.to_string()));
            }
            if let Some(page_size) = page_size {
                params.push(("limit", page_size.to_string()));
            }

            let mut url = format!("{}/api/v1/accountInactiveOrders", inner.base_url);
            if !params.is_empty() {
                let query =
                    params.iter().map(|(k, v)| format!("{k}={v}")).collect::<Vec<_>>().join("&");
                url.push('?');
                url.push_str(&query);
            }

            let response = inner
                .client
                .request(Method::GET, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Get orders history failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let orders: LighterOrdersResponse = match serde_json::from_slice(&response.body) {
                Ok(parsed) => parsed,
                Err(_) => {
                    let rows: Vec<LighterOrderResponse> = serde_json::from_slice(&response.body)?;
                    LighterOrdersResponse { orders: rows, next: None, prev: None }
                }
            };
            Ok(orders)
        })
    }

    pub fn get_fills(
        &self,
        market: Option<String>,
        start_at_ms: Option<u64>,
        end_at_ms: Option<u64>,
        page_size: Option<u32>,
    ) -> anyhow::Result<LighterFillsResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers()?;

        get_runtime().block_on(async move {
            let mut params = vec![];
            if let Some(market) = market {
                params.push(("market", market));
            }
            if let Some(start_at_ms) = start_at_ms {
                params.push(("start_at_ms", start_at_ms.to_string()));
            }
            if let Some(end_at_ms) = end_at_ms {
                params.push(("end_at_ms", end_at_ms.to_string()));
            }
            if let Some(page_size) = page_size {
                params.push(("limit", page_size.to_string()));
            }

            let mut url = format!("{}/api/v1/trades", inner.base_url);
            if !params.is_empty() {
                let query =
                    params.iter().map(|(k, v)| format!("{k}={v}")).collect::<Vec<_>>().join("&");
                url.push('?');
                url.push_str(&query);
            }

            let response = inner
                .client
                .request(Method::GET, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Get fills failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let fills: LighterFillsResponse = match serde_json::from_slice(&response.body) {
                Ok(parsed) => parsed,
                Err(_) => {
                    let rows: Vec<LighterFillResponse> = serde_json::from_slice(&response.body)?;
                    LighterFillsResponse { trades: rows, results: vec![], next: None, prev: None }
                }
            };
            Ok(fills)
        })
    }

    pub fn get_fill_by_id(&self, fill_id: String) -> anyhow::Result<Option<LighterFillResponse>> {
        let fills = self.get_fills(None, None, None, Some(200))?;
        Ok(fills
            .trades
            .iter()
            .chain(fills.results.iter())
            .find(|f| {
                f.id.as_deref() == Some(fill_id.as_str())
                    || f.trade_id.as_deref() == Some(fill_id.as_str())
            })
            .cloned())
    }
}
