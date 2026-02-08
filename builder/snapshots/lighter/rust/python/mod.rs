//! NautilusTrader Adapter - Python Bindings (PyO3)

use crate::common::urls::Endpoints;
use crate::config::LighterConfig;
use crate::http::client::LighterHttpClient;
use crate::parsing::models::{OrderBook, OrderRequest, OrderResponse, Ticker};
use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Python wrapper for the Lighter Client
#[pyclass(name = "LighterClient")]
pub struct PyLighterClient {
    client: LighterHttpClient,
}

#[pymethods]
impl PyLighterClient {
    #[new]
    #[pyo3(signature = (chain_id, api_key, api_secret))]
    pub fn new(chain_id: String, api_key: String, api_secret: String) -> PyResult<Self> {
        let config = LighterConfig::new(chain_id, api_key, api_secret);
        Ok(Self {
            client: LighterHttpClient::new(config),
        })
    }

    /// Fetch tickers for a given chain ID
    pub fn get_tickers(&self, py: Python) -> PyResult<Vec<PyObject>> {
        let path = Endpoints::tickers();
        py.allow_threads(|| {
            let runtime = tokio::runtime::Runtime::new().unwrap();
            let json_str = runtime.block_on(self.client.get(&path, Some(&"chainId=137".to_string())))?; // Example query param
            let tickers: Vec<Ticker> = serde_json::from_str(&json_str)?;
            
            let py_list = tickers.into_iter().map(|t| {
                Python::with_gil(|py| {
                    let dict = PyDict::new(py);
                    dict.set_item("symbol", t.symbol).unwrap();
                    dict.set_item("lastPrice", t.last_price).unwrap();
                    dict.set_item("volume", t.volume).unwrap();
                    dict.into()
                })
            }).collect();
            Ok(py_list)
        })
    }

    /// Fetch orderbook
    pub fn get_orderbook(&self, py: Python, symbol: String) -> PyResult<PyObject> {
        let path = Endpoints::orderbook();
        py.allow_threads(|| {
            let runtime = tokio::runtime::Runtime::new().unwrap();
            let query = format!("chainId=137&symbol={}", symbol);
            let json_str = runtime.block_on(self.client.get(&path, Some(&query)))?;
            let orderbook: OrderBook = serde_json::from_str(&json_str)?;
            
            Python::with_gil(|py| {
                let dict = PyDict::new(py);
                dict.set_item("asks", orderbook.asks).unwrap();
                dict.set_item("bids", orderbook.bids).unwrap();
                dict.set_item("timestamp", orderbook.timestamp).unwrap();
                Ok(dict.into())
            })
        })
    }

    /// Create an order
    pub fn create_order(
        &self,
        py: Python,
        symbol: String,
        side: String,
        order_type: String,
        price: String,
        quantity: String,
        client_order_id: String,
    ) -> PyResult<String> {
        let path = Endpoints::order();
        let order_req = OrderRequest {
            chain_id: "137".to_string(), // Assuming Polygon for simplicity in Python binding
            symbol,
            side,
            order_type,
            price,
            quantity,
            client_order_id,
            time_in_force: "GTC".to_string(),
        };
        
        let body = serde_json::to_string(&order_req)?;
        
        py.allow_threads(|| {
            let runtime = tokio::runtime::Runtime::new().unwrap();
            let json_str = runtime.block_on(self.client.post(&path, &body))?;
            let resp: OrderResponse = serde_json::from_str(&json_str)?;
            Ok(resp.order_id)
        })
    }
}