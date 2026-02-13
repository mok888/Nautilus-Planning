use pyo3::prelude::*;
use std::collections::HashMap;

use crate::common::credential::ParadexCredential;
use crate::http::client::ParadexHttpClient;
use nautilus_network::http::HttpClient;

#[pyclass(name = "PyParadexHttpClient")]
pub struct PyParadexHttpClient {
    client: ParadexHttpClient,
}

#[pymethods]
impl PyParadexHttpClient {
    /// Create a new Paradex HTTP client.
    ///
    /// Args:
    ///     base_url: Optional base URL override (defaults to testnet)
    ///     chain_id: Optional chain ID (defaults to PRIVATE_SN_POTC_SEPOLIA)  
    ///     starknet_account: L2 account address (hex string)
    ///     starknet_private_key: L2 private key (hex string)
    #[new]
    pub fn new(
        base_url: Option<String>,
        chain_id: Option<String>,
        starknet_account: Option<String>,
        starknet_private_key: Option<String>,
    ) -> Self {
        let base = base_url.unwrap_or_else(|| "https://api.testnet.paradex.trade/v1".to_string());
        let chain = chain_id.unwrap_or_else(|| "PRIVATE_SN_POTC_SEPOLIA".to_string());

        let credential =
            ParadexCredential::resolve(starknet_private_key, starknet_account).ok().flatten();

        let client = HttpClient::new(HashMap::new(), Vec::new(), Vec::new(), None, None, None)
            .expect("Failed to create HttpClient");

        let paradex_client = ParadexHttpClient::new(base, chain, client, credential);

        Self { client: paradex_client }
    }

    pub fn get_info(&self) -> PyResult<String> {
        self.client
            .get_info()
            .map(|info| serde_json::to_string(&info).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_orderbook(&self, market_symbol: &str) -> PyResult<String> {
        self.client
            .get_orderbook(market_symbol)
            .map(|ob| serde_json::to_string(&ob).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

    pub fn get_account_state(&self) -> PyResult<String> {
        self.client
            .get_account_state()
            .map(|state| serde_json::to_string(&state).unwrap_or_default())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("{e}")))
    }

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
