use http::Method;
use nautilus_common::live::get_runtime;
use nautilus_network::http::HttpClient;
use serde_json::json;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::common::credential::StandXCredential;
use crate::common::models::{
    StandXAccountStateResponse, StandXActionResponse, StandXFillResponse, StandXFillsResponse,
    StandXInfoResponse, StandXMarketInfo, StandXOrderResponse, StandXOrderbookResponse,
    StandXOrdersResponse, StandXTradesResponse,
};
use crate::common::symbols::normalize_symbol_to_venue;
use crate::http::signing::sign_ed25519_base64;

pub struct StandXRawHttpClient {
    base_url: String,
    client: HttpClient,
    credential: Option<StandXCredential>,
}

impl StandXRawHttpClient {
    pub fn new(base_url: String, client: HttpClient, credential: Option<StandXCredential>) -> Self {
        Self { base_url, client, credential }
    }

    pub fn base_url(&self) -> &str {
        &self.base_url
    }

    pub fn get_info(&self) -> anyhow::Result<StandXInfoResponse> {
        get_runtime().block_on(async {
            let url = format!("{}/api/query_symbol_info", self.base_url);
            let response = self
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Get info failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }

            let payload: serde_json::Value = serde_json::from_slice(&response.body)?;
            let rows = if let Some(arr) = payload.as_array() {
                arr.clone()
            } else {
                payload
                    .get("result")
                    .or_else(|| payload.get("results"))
                    .or_else(|| payload.get("markets"))
                    .and_then(|v| v.as_array())
                    .cloned()
                    .unwrap_or_default()
            };

            let mut markets = Vec::with_capacity(rows.len());
            for row in rows {
                let symbol =
                    row.get("symbol").and_then(|v| v.as_str()).unwrap_or("UNKNOWN-USD").to_string();

                let market_id = row
                    .get("market_id")
                    .or_else(|| row.get("marketId"))
                    .and_then(|v| {
                        v.as_u64().or_else(|| v.as_str().and_then(|s| s.parse::<u64>().ok()))
                    })
                    .unwrap_or(0) as u32;

                let price_decimals = row
                    .get("price_tick_decimals")
                    .or_else(|| row.get("price_decimals"))
                    .or_else(|| row.get("priceDecimals"))
                    .and_then(|v| {
                        v.as_u64().or_else(|| v.as_str().and_then(|s| s.parse::<u64>().ok()))
                    })
                    .unwrap_or(2) as u32;

                let size_decimals = row
                    .get("qty_tick_decimals")
                    .or_else(|| row.get("size_decimals"))
                    .or_else(|| row.get("sizeDecimals"))
                    .and_then(|v| {
                        v.as_u64().or_else(|| v.as_str().and_then(|s| s.parse::<u64>().ok()))
                    })
                    .unwrap_or(4) as u32;

                markets.push(StandXMarketInfo {
                    market_id,
                    symbol,
                    price_decimals,
                    size_decimals,
                    base_token_id: 0,
                    quote_token_id: 0,
                    imf: 0.0,
                    mmf: 0.0,
                    cmf: 0.0,
                });
            }

            let info = StandXInfoResponse { markets, tokens: vec![] };
            Ok(info)
        })
    }

    pub fn get_orderbook(&self, market_id: u32) -> anyhow::Result<StandXOrderbookResponse> {
        get_runtime().block_on(async {
            let url = format!("{}/market/{}/orderbook", self.base_url, market_id);
            let response = self
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let orderbook: StandXOrderbookResponse = serde_json::from_slice(&response.body)?;
            Ok(orderbook)
        })
    }

    pub fn get_trades(
        &self,
        market_id: u32,
        limit: Option<u32>,
    ) -> anyhow::Result<StandXTradesResponse> {
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
            let trades: StandXTradesResponse = serde_json::from_slice(&response.body)?;
            Ok(trades)
        })
    }

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

    pub fn submit_action(&self, payload: &str) -> anyhow::Result<StandXActionResponse> {
        let body_bytes = payload.as_bytes().to_vec();
        get_runtime().block_on(async {
            let url = format!("{}/action", self.base_url);
            let response = self
                .client
                .post(url, None, None, Some(body_bytes), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let action: StandXActionResponse = serde_json::from_slice(&response.body)?;
            Ok(action)
        })
    }
}

pub struct StandXHttpClient {
    inner: Arc<StandXRawHttpClient>,
}

impl StandXHttpClient {
    pub fn new(base_url: String, client: HttpClient, credential: Option<StandXCredential>) -> Self {
        Self { inner: Arc::new(StandXRawHttpClient::new(base_url, client, credential)) }
    }

    pub fn get_info(&self) -> anyhow::Result<StandXInfoResponse> {
        self.inner.get_info()
    }

    pub fn get_orderbook(&self, market_id: u32) -> anyhow::Result<StandXOrderbookResponse> {
        self.inner.get_orderbook(market_id)
    }

    pub fn get_trades(
        &self,
        market_id: u32,
        limit: Option<u32>,
    ) -> anyhow::Result<StandXTradesResponse> {
        self.inner.get_trades(market_id, limit)
    }

    pub fn get_timestamp(&self) -> anyhow::Result<u64> {
        self.inner.get_timestamp()
    }

    pub fn submit_action(&self, payload: &str) -> anyhow::Result<StandXActionResponse> {
        self.inner.submit_action(payload)
    }

    fn auth_headers(
        &self,
        body: Option<&serde_json::Value>,
    ) -> anyhow::Result<HashMap<String, String>> {
        let creds = self
            .inner
            .credential
            .as_ref()
            .ok_or_else(|| anyhow::anyhow!("No credentials configured"))?;

        let mut headers = HashMap::new();
        headers.insert("Authorization".to_string(), creds.authorization_header());
        headers.insert("Content-Type".to_string(), "application/json".to_string());

        if let Some(value) = body {
            let sign_version = "v1".to_string();
            let timestamp_ms = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map_err(|e| anyhow::anyhow!("timestamp error: {e}"))?
                .as_millis()
                .to_string();
            let request_id = format!("req-{}", timestamp_ms);
            let payload = serde_json::to_string(value)?;
            let message = format!("{},{},{},{}", sign_version, request_id, timestamp_ms, payload);
            let signature = sign_ed25519_base64(&creds.api_secret, message.as_bytes())
                .map_err(|e| anyhow::anyhow!("signature error: {e}"))?;
            headers.insert("x-request-sign-version".to_string(), sign_version);
            headers.insert("x-request-id".to_string(), request_id.clone());
            headers.insert("x-request-timestamp".to_string(), timestamp_ms);
            headers.insert("x-request-signature".to_string(), signature);
            headers.insert("x-session-id".to_string(), request_id);
        }

        Ok(headers)
    }

    pub fn get_account_state(&self) -> anyhow::Result<StandXAccountStateResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers(None)?;
        get_runtime().block_on(async move {
            let url = format!("{}/api/query_balance", inner.base_url);
            let response = inner
                .client
                .request(Method::GET, url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8>");
                return Err(anyhow::anyhow!(
                    "Get account state failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }
            let account: StandXAccountStateResponse = serde_json::from_slice(&response.body)?;
            Ok(account)
        })
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
        _signature_timestamp_ms: Option<u64>,
    ) -> anyhow::Result<StandXActionResponse> {
        let inner = self.inner.clone();
        let market = normalize_symbol_to_venue(&market);
        let side = side.to_ascii_lowercase();
        let order_type = order_type.to_ascii_lowercase();
        let instruction = instruction.map(|s| s.to_ascii_lowercase());
        let payload = json!({
            "symbol": market,
            "side": side,
            "order_type": order_type,
            "qty": size,
            "price": price,
            "cl_ord_id": client_id,
            "time_in_force": instruction,
            "trigger_price": trigger_price,
            "reduce_only": reduce_only,
        });
        let headers = self.auth_headers(Some(&payload))?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/new_order", inner.base_url);
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
            Ok(StandXActionResponse {
                action_id: value
                    .get("action_id")
                    .or_else(|| value.get("id"))
                    .and_then(|v| v.as_str())
                    .unwrap_or_default()
                    .to_string(),
                status: value
                    .get("status")
                    .and_then(|v| v.as_str())
                    .unwrap_or("submitted")
                    .to_string(),
                tx_signature: value
                    .get("tx_signature")
                    .or_else(|| value.get("signature"))
                    .and_then(|v| v.as_str())
                    .map(str::to_string),
                id: value.get("id").and_then(|v| v.as_str()).map(str::to_string),
                client_id: value
                    .get("cl_ord_id")
                    .or_else(|| value.get("client_order_id"))
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
        let payload = json!({
            "cl_ord_id": client_id,
            "symbol": market.map(|symbol| normalize_symbol_to_venue(&symbol)),
        });
        let headers = self.auth_headers(Some(&payload))?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/cancel_order", inner.base_url);
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
        let payload = if let Ok(order_id_num) = order_id.parse::<i64>() {
            json!({ "order_id": order_id_num })
        } else {
            json!({ "order_id": order_id })
        };
        let headers = self.auth_headers(Some(&payload))?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/cancel_order", inner.base_url);
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
                return Err(anyhow::anyhow!("Cancel failed {:?}: {}", response.status, body_text));
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
        _signature_timestamp_ms: Option<u64>,
    ) -> anyhow::Result<StandXOrderResponse> {
        let inner = self.inner.clone();
        let market = normalize_symbol_to_venue(&market);
        let side = side.to_ascii_lowercase();
        let order_type = order_type.to_ascii_lowercase();
        let payload = json!({
            "order_id": order_id,
            "symbol": market,
            "side": side,
            "order_type": order_type,
            "qty": size,
            "price": price,
            "trigger_price": trigger_price,
            "time_in_force": "gtc",
            "reduce_only": false,
        });
        let headers = self.auth_headers(Some(&payload))?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/new_order", inner.base_url);
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
                    "Modify order failed {:?}: {}",
                    response.status,
                    body_text
                ));
            }
            let order: StandXOrderResponse = serde_json::from_slice(&response.body)?;
            Ok(order)
        })
    }

    pub fn cancel_all_orders(&self, market: Option<String>) -> anyhow::Result<()> {
        let open_orders = self.get_open_orders(market.clone())?;
        let mut errors: Vec<String> = Vec::new();

        for order in open_orders {
            let order_market =
                order.symbol.clone().or_else(|| order.market.clone()).or_else(|| market.clone());
            let client_id = order
                .client_order_id
                .clone()
                .or_else(|| order.client_order_index.clone())
                .or_else(|| order.client_id.clone());
            let order_id = order
                .order_index
                .clone()
                .or_else(|| order.order_id.clone())
                .or_else(|| order.id.clone());

            let result = if let Some(client_id) = client_id {
                self.cancel_order_by_client_id(client_id, order_market)
            } else if let Some(order_id) = order_id {
                self.cancel_order(order_id)
            } else {
                Err(anyhow::anyhow!("Order missing both client and venue IDs"))
            };

            if let Err(e) = result {
                errors.push(e.to_string());
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(anyhow::anyhow!("Cancel all encountered errors: {}", errors.join(" | ")))
        }
    }

    pub fn get_open_orders(
        &self,
        market: Option<String>,
    ) -> anyhow::Result<Vec<StandXOrderResponse>> {
        let inner = self.inner.clone();
        let headers = self.auth_headers(None)?;

        get_runtime().block_on(async move {
            let mut url = format!("{}/api/query_open_orders", inner.base_url);
            if let Some(market) = market {
                let symbol = normalize_symbol_to_venue(&market);
                url.push_str(&format!("?symbol={symbol}"));
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
            let parsed: serde_json::Value = serde_json::from_slice(&response.body)?;
            let rows = if let Some(arr) = parsed.as_array() {
                arr.clone()
            } else {
                parsed
                    .get("result")
                    .or_else(|| parsed.get("results"))
                    .or_else(|| parsed.get("orders"))
                    .and_then(|v| v.as_array())
                    .cloned()
                    .unwrap_or_default()
            };

            let mut out = Vec::with_capacity(rows.len());
            for row in rows {
                out.push(serde_json::from_value::<StandXOrderResponse>(row)?);
            }
            Ok(out)
        })
    }

    pub fn get_order_by_id(&self, order_id: String) -> anyhow::Result<StandXOrderResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers(None)?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/query_order?order_id={}", inner.base_url, order_id);
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
            let parsed: serde_json::Value = serde_json::from_slice(&response.body)?;
            let payload = parsed.get("result").cloned().unwrap_or(parsed);
            let order: StandXOrderResponse = serde_json::from_value(payload)?;
            Ok(order)
        })
    }

    pub fn get_order_by_client_id(&self, client_id: String) -> anyhow::Result<StandXOrderResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers(None)?;

        get_runtime().block_on(async move {
            let url = format!("{}/api/query_order?cl_ord_id={}", inner.base_url, client_id);
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
            let parsed: serde_json::Value = serde_json::from_slice(&response.body)?;
            let payload = parsed.get("result").cloned().unwrap_or(parsed);
            let order: StandXOrderResponse = serde_json::from_value(payload)?;
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
    ) -> anyhow::Result<StandXOrdersResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers(None)?;

        get_runtime().block_on(async move {
            let mut params = vec![];
            if let Some(market) = market {
                params.push(("symbol", normalize_symbol_to_venue(&market)));
            }
            if let Some(client_id) = client_id {
                params.push(("cl_ord_id", client_id));
            }
            let _ = start_at_ms;
            let _ = end_at_ms;
            if let Some(page_size) = page_size {
                params.push(("limit", page_size.to_string()));
            }

            let mut url = format!("{}/api/query_orders", inner.base_url);
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
            let parsed: serde_json::Value = serde_json::from_slice(&response.body)?;
            let rows = if let Some(arr) = parsed.as_array() {
                arr.clone()
            } else {
                parsed
                    .get("result")
                    .or_else(|| parsed.get("results"))
                    .or_else(|| parsed.get("orders"))
                    .and_then(|v| v.as_array())
                    .cloned()
                    .unwrap_or_default()
            };
            let mut normalized = Vec::with_capacity(rows.len());
            for row in rows {
                normalized.push(serde_json::from_value::<StandXOrderResponse>(row)?);
            }
            let orders = StandXOrdersResponse {
                orders: vec![],
                result: normalized,
                results: vec![],
                next: parsed.get("next").and_then(|v| v.as_str()).map(str::to_string),
                prev: parsed.get("prev").and_then(|v| v.as_str()).map(str::to_string),
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
    ) -> anyhow::Result<StandXFillsResponse> {
        let inner = self.inner.clone();
        let headers = self.auth_headers(None)?;

        get_runtime().block_on(async move {
            let mut params = vec![];
            if let Some(market) = market {
                params.push(("symbol", normalize_symbol_to_venue(&market)));
            }
            let _ = start_at_ms;
            let _ = end_at_ms;
            if let Some(page_size) = page_size {
                params.push(("limit", page_size.to_string()));
            }

            let mut url = format!("{}/api/query_trades", inner.base_url);
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

            let parsed: serde_json::Value = serde_json::from_slice(&response.body)?;
            let rows = if let Some(arr) = parsed.as_array() {
                arr.clone()
            } else {
                parsed
                    .get("result")
                    .or_else(|| parsed.get("results"))
                    .or_else(|| parsed.get("trades"))
                    .and_then(|v| v.as_array())
                    .cloned()
                    .unwrap_or_default()
            };
            let mut normalized = Vec::with_capacity(rows.len());
            for row in rows {
                normalized.push(serde_json::from_value::<StandXFillResponse>(row)?);
            }

            let fills = StandXFillsResponse {
                trades: vec![],
                result: normalized,
                results: vec![],
                next: parsed.get("next").and_then(|v| v.as_str()).map(str::to_string),
                prev: parsed.get("prev").and_then(|v| v.as_str()).map(str::to_string),
            };
            Ok(fills)
        })
    }

    pub fn get_fill_by_id(&self, fill_id: String) -> anyhow::Result<Option<StandXFillResponse>> {
        let fills = self.get_fills(None, None, None, Some(200))?;
        Ok(fills
            .trades
            .iter()
            .chain(fills.result.iter())
            .chain(fills.results.iter())
            .find(|f| {
                f.id.as_deref() == Some(fill_id.as_str())
                    || f.trade_id.as_deref() == Some(fill_id.as_str())
            })
            .cloned())
    }
}
