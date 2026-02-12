use http::Method;
use nautilus_common::live::get_runtime;
use nautilus_network::http::HttpClient;
use serde_json::json;
use std::collections::HashMap;
use std::sync::Arc;
use std::sync::Mutex;

use crate::common::credential::ParadexCredential;
use crate::common::models::{
    ParadexActionResponse, ParadexFillResponse, ParadexFillsResponse, ParadexInfoResponse,
    ParadexOrderResponse, ParadexOrderbookResponse, ParadexOrdersResponse, ParadexTradesResponse,
};
use crate::http::signing::{
    sign_auth_message, sign_modify_order, sign_order, ModifyOrderParams, OrderParams,
};

/// Stored JWT and when it was obtained.
struct AuthState {
    jwt: String,
    auth_timestamp: u64, // seconds since epoch
}

/// Raw HTTP client matching Paradex venue API endpoints.
pub struct ParadexRawHttpClient {
    base_url: String,
    chain_id: String,
    client: HttpClient,
    credential: Option<ParadexCredential>,
    auth_state: Mutex<Option<AuthState>>,
}

/// Domain HTTP client exposing Nautilus types.
pub struct ParadexHttpClient {
    inner: Arc<ParadexRawHttpClient>,
}

impl ParadexHttpClient {
    pub fn new(
        base_url: String,
        chain_id: String,
        client: HttpClient,
        credential: Option<ParadexCredential>,
    ) -> Self {
        Self {
            inner: Arc::new(ParadexRawHttpClient {
                base_url,
                chain_id,
                client,
                credential,
                auth_state: Mutex::new(None),
            }),
        }
    }

    /// Authenticate with Paradex using L2 wallet signing.
    /// POST /auth/{hex(pubkey)} with StarkNet headers → returns JWT.
    fn authenticate(&self) -> anyhow::Result<String> {
        let inner = self.inner.clone();
        let creds = inner
            .credential
            .as_ref()
            .ok_or_else(|| anyhow::anyhow!("No credentials configured"))?;

        // Check if we have a valid JWT (< 4 minutes old)
        {
            let state = inner.auth_state.lock().unwrap();
            if let Some(ref auth) = *state {
                let now =
                    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs();
                if now - auth.auth_timestamp < 4 * 60 {
                    return Ok(auth.jwt.clone());
                }
            }
        }

        // Need fresh JWT
        let timestamp =
            std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs();
        let expiration = timestamp + 24 * 60 * 60; // +24h

        let pk = &creds.starknet_private_key;
        let addr = &creds.starknet_account_address;

        let pubkey_hex = creds
            .public_key_hex()
            .map_err(|e| anyhow::anyhow!("Failed to derive public key: {}", e))?;

        // Sign auth message
        let signature = sign_auth_message(pk, addr, &inner.chain_id, timestamp, expiration)
            .map_err(|e| anyhow::anyhow!("Auth signing error: {}", e))?;

        let url = format!("{}/auth/{}", inner.base_url, pubkey_hex);

        let jwt = get_runtime().block_on(async {
            let mut headers = HashMap::new();
            headers.insert("PARADEX-STARKNET-ACCOUNT".to_string(), addr.clone());
            headers.insert("PARADEX-STARKNET-SIGNATURE".to_string(), signature.clone());
            headers.insert("PARADEX-TIMESTAMP".to_string(), timestamp.to_string());
            headers.insert("PARADEX-SIGNATURE-EXPIRATION".to_string(), expiration.to_string());

            let response = inner
                .client
                .post(url, None, Some(headers), None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("Auth request error: {e}"))?;

            if !response.status.is_success() {
                let body_text = std::str::from_utf8(&response.body).unwrap_or("<non-utf8 body>");
                return Err(anyhow::anyhow!("Auth failed {:?}: {}", response.status, body_text));
            }

            let body: serde_json::Value = serde_json::from_slice(&response.body)?;
            let jwt = body["jwt_token"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("No jwt_token in auth response: {}", body))?
                .to_string();
            Ok(jwt)
        })?;

        // Store JWT
        {
            let mut state = inner.auth_state.lock().unwrap();
            *state = Some(AuthState { jwt: jwt.clone(), auth_timestamp: timestamp });
        }

        Ok(jwt)
    }

    /// Fetch exchange info including markets.
    /// GET /markets
    pub fn get_info(&self) -> anyhow::Result<ParadexInfoResponse> {
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            let url = format!("{}/markets", inner.base_url);
            let response = inner
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let info: ParadexInfoResponse = serde_json::from_slice(&response.body)?;
            Ok(info)
        })
    }

    /// Fetch orderbook for a given market.
    /// GET /orderbook/{market_symbol}
    pub fn get_orderbook(&self, market_symbol: &str) -> anyhow::Result<ParadexOrderbookResponse> {
        let inner = self.inner.clone();
        let symbol = market_symbol.to_string();
        get_runtime().block_on(async move {
            let url = format!("{}/orderbook/{}", inner.base_url, symbol);
            let response = inner
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let orderbook: ParadexOrderbookResponse = serde_json::from_slice(&response.body)?;
            Ok(orderbook)
        })
    }

    /// Fetch recent trades.
    /// GET /trades
    pub fn get_trades(
        &self,
        market_id: u32,
        limit: Option<u32>,
    ) -> anyhow::Result<ParadexTradesResponse> {
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            let mut url = format!("{}/trades?market_id={}", inner.base_url, market_id);
            if let Some(limit) = limit {
                url.push_str(&format!("&limit={}", limit));
            }
            let response = inner
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let trades: ParadexTradesResponse = serde_json::from_slice(&response.body)?;
            Ok(trades)
        })
    }

    /// Get server timestamp.
    /// GET /timestamp
    pub fn get_timestamp(&self) -> anyhow::Result<u64> {
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            let url = format!("{}/timestamp", inner.base_url);
            let response = inner
                .client
                .get(url, None, None, None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;
            let body_str = std::str::from_utf8(&response.body)?;
            let ts: u64 = body_str.trim().parse()?;
            Ok(ts)
        })
    }

    /// Submit a new order.
    /// POST /orders (requires JWT obtained via authenticate())
    pub fn submit_order(
        &self,
        market: String,
        side: String,       // "BUY" or "SELL"
        order_type: String, // "LIMIT" or "MARKET"
        size: String,       // Decimal string (e.g. "0.01")
        price: String,      // Decimal string (e.g. "50000")
        client_id: Option<String>,
        instruction: Option<String>,
        trigger_price: Option<String>,
        reduce_only: bool,
        signature_timestamp_ms: Option<u64>,
    ) -> anyhow::Result<ParadexActionResponse> {
        let inner = self.inner.clone();

        let creds = inner
            .credential
            .as_ref()
            .ok_or_else(|| anyhow::anyhow!("No credentials configured"))?;

        // 1. Authenticate (obtain/refresh JWT)
        let jwt = self.authenticate()?;

        let pk = &creds.starknet_private_key;
        let addr = &creds.starknet_account_address;

        // 2. Prepare Order Params
        // Order timestamp is in MILLISECONDS (acts as nonce)
        let timestamp_ms = match signature_timestamp_ms {
            Some(ts) => ts,
            None => std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_millis()
                as u64,
        };

        let side_chain = match side.to_uppercase().as_str() {
            "BUY" => "1".to_string(),
            "SELL" => "2".to_string(),
            val => val.to_string(),
        };

        // Convert size/price to quantum (x 10^8) as integer strings
        let size_quantum = decimal_to_quantum(&size);
        let price_quantum = if order_type.to_uppercase() == "MARKET" {
            "0".to_string()
        } else {
            decimal_to_quantum(&price)
        };

        let params = OrderParams {
            chain_id: inner.chain_id.clone(),
            timestamp: timestamp_ms,
            market: market.clone(),
            side: side_chain.clone(),
            order_type: order_type.clone(),
            size: size_quantum,
            price: price_quantum,
        };

        // 3. Sign Order
        let signature =
            sign_order(pk, addr, params).map_err(|e| anyhow::anyhow!("Sign Order Error: {}", e))?;

        // 4. Build JSON Payload (matches paradex-py Order.dump_to_dict())
        let order_type_upper = order_type.to_uppercase();
        let mut payload = json!({
            "market": market,
            "side": side.to_uppercase(),
            "type": order_type_upper,
            "size": size,
            "signature": signature,
            "signature_timestamp": timestamp_ms,
            "instruction": instruction.unwrap_or_else(|| "GTC".to_string())
        });

        let include_price = !matches!(
            order_type_upper.as_str(),
            "MARKET" | "STOP_MARKET" | "STOP_LOSS_MARKET" | "TAKE_PROFIT_MARKET"
        );
        if include_price {
            payload["price"] = serde_json::Value::String(price);
        }

        if let Some(client_id) = client_id {
            payload["client_id"] = serde_json::Value::String(client_id);
        }

        if let Some(trigger_price) = trigger_price {
            payload["trigger_price"] = serde_json::Value::String(trigger_price);
        }

        if reduce_only {
            payload["flags"] = serde_json::json!(["REDUCE_ONLY"]);
        }

        let payload_json = payload.to_string();

        let payload_bytes = payload_json.as_bytes().to_vec();

        // 5. Send Request with JWT Authorization
        get_runtime().block_on(async {
            let url = format!("{}/orders", inner.base_url);

            let mut headers = HashMap::new();
            headers.insert("Content-Type".to_string(), "application/json".to_string());
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .post(url, None, Some(headers), Some(payload_bytes), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            let body: serde_json::Value = serde_json::from_slice(&response.body)?;
            let action = ParadexActionResponse {
                action_id: body.get("action_id").and_then(|v| v.as_str()).map(|s| s.to_string()),
                status: body.get("status").and_then(|v| v.as_str()).map(|s| s.to_string()),
                tx_signature: body
                    .get("tx_signature")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string()),
                id: body.get("id").and_then(|v| v.as_str()).map(|s| s.to_string()),
                client_id: body.get("client_id").and_then(|v| v.as_str()).map(|s| s.to_string()),
            };
            Ok(action)
        })
    }

    pub fn cancel_order_by_client_id(
        &self,
        client_id: String,
        market: Option<String>,
    ) -> anyhow::Result<()> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let mut url = format!("{}/orders/by_client_id/{}", inner.base_url, client_id);
            if let Some(market) = market {
                url.push_str("?market=");
                url.push_str(&market);
            }

            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .delete(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
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
    ) -> anyhow::Result<ParadexOrderResponse> {
        let inner = self.inner.clone();

        let creds = inner
            .credential
            .as_ref()
            .ok_or_else(|| anyhow::anyhow!("No credentials configured"))?;

        let jwt = self.authenticate()?;

        let pk = &creds.starknet_private_key;
        let addr = &creds.starknet_account_address;

        let timestamp_ms = match signature_timestamp_ms {
            Some(ts) => ts,
            None => std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_millis()
                as u64,
        };

        let side_chain = match side.to_uppercase().as_str() {
            "BUY" => "1".to_string(),
            "SELL" => "2".to_string(),
            val => val.to_string(),
        };

        let size_quantum = decimal_to_quantum(&size);
        let price_quantum = if order_type.to_uppercase() == "MARKET" {
            "0".to_string()
        } else {
            decimal_to_quantum(&price)
        };

        let params = ModifyOrderParams {
            chain_id: inner.chain_id.clone(),
            timestamp: timestamp_ms,
            market: market.clone(),
            side: side_chain,
            order_type: order_type.clone(),
            size: size_quantum,
            price: price_quantum,
            id: order_id.clone(),
        };

        let signature = sign_modify_order(pk, addr, params)
            .map_err(|e| anyhow::anyhow!("Sign Modify Error: {}", e))?;

        let mut payload = json!({
            "id": order_id,
            "market": market,
            "side": side.to_uppercase(),
            "type": order_type.to_uppercase(),
            "size": size,
            "price": price,
            "signature": signature,
            "signature_timestamp": timestamp_ms,
        });

        if let Some(trigger_price) = trigger_price {
            payload["trigger_price"] = serde_json::Value::String(trigger_price);
        }

        let payload_bytes = payload.to_string().as_bytes().to_vec();

        get_runtime().block_on(async move {
            let url = format!("{}/orders/{}", inner.base_url, order_id);

            let mut headers = HashMap::new();
            headers.insert("Content-Type".to_string(), "application/json".to_string());
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .request(Method::PUT, url, None, Some(headers), Some(payload_bytes), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            let order: ParadexOrderResponse = serde_json::from_slice(&response.body)?;
            Ok(order)
        })
    }

    pub fn cancel_order(&self, order_id: String) -> anyhow::Result<()> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let url = format!("{}/orders/{}", inner.base_url, order_id);

            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .delete(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            Ok(())
        })
    }

    pub fn cancel_all_orders(&self, market: Option<String>) -> anyhow::Result<()> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let mut url = format!("{}/orders", inner.base_url);
            if let Some(market) = market {
                url.push_str("?market=");
                url.push_str(&market);
            }

            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .delete(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            Ok(())
        })
    }

    pub fn get_order_by_id(&self, order_id: String) -> anyhow::Result<ParadexOrderResponse> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let url = format!("{}/orders/{}", inner.base_url, order_id);
            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .get(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            let order: ParadexOrderResponse = serde_json::from_slice(&response.body)?;
            Ok(order)
        })
    }

    pub fn get_order_by_client_id(
        &self,
        client_id: String,
    ) -> anyhow::Result<ParadexOrderResponse> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let url = format!("{}/orders/by_client_id/{}", inner.base_url, client_id);
            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .get(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            let order: ParadexOrderResponse = serde_json::from_slice(&response.body)?;
            Ok(order)
        })
    }

    pub fn get_open_orders(
        &self,
        market: Option<String>,
    ) -> anyhow::Result<Vec<ParadexOrderResponse>> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let mut url = format!("{}/orders", inner.base_url);
            if let Some(market) = market {
                url.push_str("?market=");
                url.push_str(&market);
            }

            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .get(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            let body: serde_json::Value = serde_json::from_slice(&response.body)?;
            if body.get("results").is_some() {
                let payload: ParadexOrdersResponse = serde_json::from_value(body)?;
                return Ok(payload.results);
            }

            if body.is_array() {
                let orders: Vec<ParadexOrderResponse> = serde_json::from_value(body)?;
                return Ok(orders);
            }

            Err(anyhow::anyhow!("Unexpected open orders payload"))
        })
    }

    pub fn get_orders_history(
        &self,
        market: Option<String>,
        client_id: Option<String>,
        start_at_ms: Option<u64>,
        end_at_ms: Option<u64>,
        page_size: Option<u32>,
    ) -> anyhow::Result<ParadexOrdersResponse> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let mut params: Vec<String> = Vec::new();
            if let Some(market) = market {
                params.push(format!("market={}", market));
            }
            if let Some(client_id) = client_id {
                params.push(format!("client_id={}", client_id));
            }
            if let Some(start_at_ms) = start_at_ms {
                params.push(format!("start_at={}", start_at_ms));
            }
            if let Some(end_at_ms) = end_at_ms {
                params.push(format!("end_at={}", end_at_ms));
            }
            if let Some(page_size) = page_size {
                params.push(format!("page_size={}", page_size));
            }

            let mut url = format!("{}/orders-history", inner.base_url);
            if !params.is_empty() {
                url.push('?');
                url.push_str(&params.join("&"));
            }

            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .get(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            let payload: ParadexOrdersResponse = serde_json::from_slice(&response.body)?;
            Ok(payload)
        })
    }

    pub fn get_fills(
        &self,
        market: Option<String>,
        start_at_ms: Option<u64>,
        end_at_ms: Option<u64>,
        page_size: Option<u32>,
    ) -> anyhow::Result<ParadexFillsResponse> {
        let inner = self.inner.clone();
        let jwt = self.authenticate()?;

        get_runtime().block_on(async move {
            let mut params: Vec<String> = Vec::new();
            if let Some(market) = market {
                params.push(format!("market={}", market));
            }
            if let Some(start_at_ms) = start_at_ms {
                params.push(format!("start_at={}", start_at_ms));
            }
            if let Some(end_at_ms) = end_at_ms {
                params.push(format!("end_at={}", end_at_ms));
            }
            if let Some(page_size) = page_size {
                params.push(format!("page_size={}", page_size));
            }

            let mut url = format!("{}/fills", inner.base_url);
            if !params.is_empty() {
                url.push('?');
                url.push_str(&params.join("&"));
            }

            let mut headers = HashMap::new();
            headers.insert("Authorization".to_string(), format!("Bearer {}", jwt));

            let response = inner
                .client
                .get(url, None, Some(headers), None, None)
                .await
                .map_err(|e| anyhow::anyhow!("{e}"))?;

            if !response.status.is_success() {
                let err_msg = std::str::from_utf8(&response.body).unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("API Error {:?}: {}", response.status, err_msg));
            }

            let payload: ParadexFillsResponse = serde_json::from_slice(&response.body)?;
            Ok(payload)
        })
    }

    pub fn get_fill_by_id(&self, fill_id: String) -> anyhow::Result<Option<ParadexFillResponse>> {
        let fills = self.get_fills(None, None, None, Some(200))?;
        Ok(fills.results.into_iter().find(|fill| fill.id.as_deref() == Some(fill_id.as_str())))
    }
}

/// Convert a decimal string like "0.01" to quantum integer string (x 10^8).
/// e.g. "0.01" → "1000000", "50000" → "5000000000000"
fn decimal_to_quantum(value: &str) -> String {
    let s = value.trim();
    if s.is_empty() || s.starts_with('-') {
        return "0".to_string();
    }

    let (int_part, frac_part) = match s.split_once('.') {
        Some((i, f)) => (i, f),
        None => (s, ""),
    };

    let int_val: u128 = int_part.parse().unwrap_or(0);

    let mut frac_8 = String::new();
    for c in frac_part.chars().take(8) {
        if !c.is_ascii_digit() {
            return "0".to_string();
        }
        frac_8.push(c);
    }
    while frac_8.len() < 8 {
        frac_8.push('0');
    }

    let frac_val: u128 = frac_8.parse().unwrap_or(0);
    (int_val.saturating_mul(100_000_000).saturating_add(frac_val)).to_string()
}
