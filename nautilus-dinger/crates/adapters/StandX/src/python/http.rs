use pyo3::prelude::*;
use std::collections::HashMap;

use crate::common::credential::StandXCredential;
use crate::http::client::{StandXHttpClient, StandXRawHttpClient};
use nautilus_network::http::HttpClient;

#[pyclass(name = "PyStandXRawHttpClient")]
pub struct PyStandXRawHttpClient {
    client: StandXRawHttpClient,
}

#[pymethods]
impl PyStandXRawHttpClient {
    #[new]
    pub fn new(
        base_url: Option<String>,
        api_key: Option<String>,
        api_secret: Option<String>,
    ) -> Self {
        let base = base_url.unwrap_or_else(|| "https://perps.standx.com".to_string());
        let credential = StandXCredential::resolve(api_key, api_secret).ok().flatten();
        let client = HttpClient::new(HashMap::new(), Vec::new(), Vec::new(), None, None, None)
            .expect("Failed to create HttpClient");
        let standx_client = StandXRawHttpClient::new(base, client, credential);
        Self { client: standx_client }
    }

    pub fn get_base_url(&self) -> &str {
        self.client.base_url()
    }

    pub fn get_info(&self) -> PyResult<String> {
        self.client
            .get_info()
            .map(|info| serde_json::to_string(&info).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_orderbook(&self, market_id: u32) -> PyResult<String> {
        self.client
            .get_orderbook(market_id)
            .map(|ob| serde_json::to_string(&ob).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_trades(&self, market_id: u32, limit: Option<u32>) -> PyResult<String> {
        self.client
            .get_trades(market_id, limit)
            .map(|trades| serde_json::to_string(&trades).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_timestamp(&self) -> PyResult<u64> {
        self.client
            .get_timestamp()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn submit_action(&self, payload: String) -> PyResult<String> {
        self.client
            .submit_action(&payload)
            .map(|action| serde_json::to_string(&action).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }
}

#[pyclass(name = "PyStandXHttpClient")]
pub struct PyStandXHttpClient {
    client: StandXHttpClient,
    base_url: String,
}

#[pymethods]
impl PyStandXHttpClient {
    #[new]
    pub fn new(
        base_url: Option<String>,
        api_key: Option<String>,
        api_secret: Option<String>,
    ) -> Self {
        let base = base_url.unwrap_or_else(|| "https://perps.standx.com".to_string());
        let credential = StandXCredential::resolve(api_key, api_secret).ok().flatten();
        let client = HttpClient::new(HashMap::new(), Vec::new(), Vec::new(), None, None, None)
            .expect("Failed to create HttpClient");
        let standx_client = StandXHttpClient::new(base.clone(), client, credential);
        Self { client: standx_client, base_url: base }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }

    pub fn get_info(&self) -> PyResult<String> {
        self.client
            .get_info()
            .map(|info| serde_json::to_string(&info).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_orderbook(&self, market_id: u32) -> PyResult<String> {
        self.client
            .get_orderbook(market_id)
            .map(|ob| serde_json::to_string(&ob).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_trades(&self, market_id: u32, limit: Option<u32>) -> PyResult<String> {
        self.client
            .get_trades(market_id, limit)
            .map(|trades| serde_json::to_string(&trades).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_timestamp(&self) -> PyResult<u64> {
        self.client
            .get_timestamp()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn submit_action(&self, payload: String) -> PyResult<String> {
        self.client
            .submit_action(&payload)
            .map(|action| serde_json::to_string(&action).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_account_state(&self) -> PyResult<String> {
        self.client
            .get_account_state()
            .map(|state| serde_json::to_string(&state).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
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
        reduce_only: Option<bool>,
        signature_timestamp_ms: Option<u64>,
    ) -> PyResult<String> {
        self.client
            .submit_order(
                market,
                side,
                order_type,
                size,
                price,
                client_id,
                instruction,
                trigger_price,
                reduce_only.unwrap_or(false),
                signature_timestamp_ms,
            )
            .map(|action| serde_json::to_string(&action).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn cancel_order_by_client_id(
        &self,
        client_id: String,
        market: Option<String>,
    ) -> PyResult<()> {
        self.client
            .cancel_order_by_client_id(client_id, market)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn cancel_order(&self, order_id: String) -> PyResult<()> {
        self.client
            .cancel_order(order_id)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
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
    ) -> PyResult<String> {
        self.client
            .modify_order(
                order_id,
                market,
                side,
                order_type,
                size,
                price,
                trigger_price,
                signature_timestamp_ms,
            )
            .map(|order| serde_json::to_string(&order).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn cancel_all_orders(&self, market: Option<String>) -> PyResult<()> {
        self.client
            .cancel_all_orders(market)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_open_orders(&self, market: Option<String>) -> PyResult<String> {
        self.client
            .get_open_orders(market)
            .map(|orders| serde_json::to_string(&orders).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_order_by_id(&self, order_id: String) -> PyResult<String> {
        self.client
            .get_order_by_id(order_id)
            .map(|order| serde_json::to_string(&order).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_order_by_client_id(&self, client_id: String) -> PyResult<String> {
        self.client
            .get_order_by_client_id(client_id)
            .map(|order| serde_json::to_string(&order).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_orders_history(
        &self,
        market: Option<String>,
        client_id: Option<String>,
        start_at_ms: Option<u64>,
        end_at_ms: Option<u64>,
        page_size: Option<u32>,
    ) -> PyResult<String> {
        self.client
            .get_orders_history(market, client_id, start_at_ms, end_at_ms, page_size)
            .map(|orders| serde_json::to_string(&orders).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_fills(
        &self,
        market: Option<String>,
        start_at_ms: Option<u64>,
        end_at_ms: Option<u64>,
        page_size: Option<u32>,
    ) -> PyResult<String> {
        self.client
            .get_fills(market, start_at_ms, end_at_ms, page_size)
            .map(|fills| serde_json::to_string(&fills).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }
}
