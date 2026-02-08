use crate::config::LighterConfig;
use crate::http::HttpClient;
use crate::parsing::models::{CreateOrderRequest, OrderResponse, Ticker};
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use std::collections::HashMap;

#[pyclass(name = "LighterConfig")]
#[derive(Clone)]
pub struct PyLighterConfig {
    #[pyo3(get, set)]
    pub api_key: String,
    #[pyo3(get, set)]
    pub secret_key: String,
    #[pyo3(get, set)]
    pub chain_id: Option<String>,
    #[pyo3(get, set)]
    pub base_url: Option<String>,
}

impl From<PyLighterConfig> for LighterConfig {
    fn from(val: PyLighterConfig) -> Self {
        LighterConfig {
            api_key: val.api_key,
            secret_key: val.secret_key,
            chain_id: val.chain_id.unwrap_or_else(|| "137".to_string()),
            base_url: val.base_url.unwrap_or_else(|| "https://api.lighter.xyz".to_string()),
            ws_url: "wss://api.lighter.xyz/ws".to_string(),
        }
    }
}

#[pyclass(name = "LighterClient")]
pub struct PyLighterClient {
    inner: HttpClient,
}

#[pymethods]
impl PyLighterClient {
    #[new]
    fn new(config: PyLighterConfig) -> PyResult<Self> {
        let rust_config = LighterConfig::from(config);
        Ok(Self {
            inner: HttpClient::new(rust_config),
        })
    }

    fn get_tickers(&self, py: Python) -> PyResult<Vec<HashMap<String, String>>> {
        py.allow_threads(|| {
            tokio::runtime::Runtime::new()
                .map_err(|e| PyException::new_err(e.to_string()))?
                .block_on(async {
                    let tickers = self.inner.get_tickers().await
                        .map_err(|e| PyException::new_err(e.to_string()))?;
                    
                    Ok(tickers.into_iter().map(|t| {
                        let mut map = HashMap::new();
                        map.insert("symbol".to_string(), t.symbol);
                        map.insert("lastPrice".to_string(), t.last_price);
                        map.insert("volume".to_string(), t.volume);
                        map.insert("priceStep".to_string(), t.price_step);
                        map.insert("sizeStep".to_string(), t.size_step);
                        map
                    }).collect())
                })
        })
    }

    fn create_order(&self, py: Python, symbol: String, side: String, price: String, quantity: String, client_order_id: String) -> PyResult<HashMap<String, String>> {
        py.allow_threads(|| {
            let req = CreateOrderRequest {
                chain_id: self.inner.config.chain_id.clone(), // Accessing internal config detail for brevity
                symbol,
                side,
                order_type: "LIMIT".to_string(), // Default for this stub
                price,
                quantity,
                client_order_id,
                tif: "GTC".to_string(),
            };
            
            tokio::runtime::Runtime::new()
                .map_err(|e| PyException::new_err(e.to_string()))?
                .block_on(async {
                    let res = self.inner.create_order(req).await
                        .map_err(|e| PyException::new_err(e.to_string()))?;
                    
                    let mut map = HashMap::new();
                    map.insert("orderId".to_string(), res.order_id);
                    map.insert("status".to_string(), res.status);
                    map.insert("symbol".to_string(), res.symbol);
                    Ok(map)
                })
        })
    }
}

#[pymodule]
fn nautilus_lighter(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyLighterConfig>()?;
    m.add_class::<PyLighterClient>()?;
    Ok(())
}