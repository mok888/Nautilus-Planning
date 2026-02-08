use pyo3::prelude::*;
use pyo3::types::PyDict;
use crate::config::{Credential, LighterConfig};
use crate::http::client::HttpClient;
use crate::parsing::models::Ticker;

#[pymodule]
fn lighter_adapter(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyLighterClient>()?;
    Ok(())
}

#[pyclass(name = "LighterClient")]
pub struct PyLighterClient {
    client: HttpClient,
}

#[pymethods]
impl PyLighterClient {
    #[new]
    #[pyo3(signature = (api_key=None, api_secret=None, chain_id="137"))] 
    fn new(api_key: Option<String>, api_secret: Option<String>, chain_id: String) -> PyResult<Self> {
        let config = LighterConfig {
            api_key: api_key.clone(),
            api_secret: api_secret.clone(),
            chain_id,
            base_url: "https://api.lighter.xyz".to_string(),
            ws_url: "wss://api.lighter.xyz/ws".to_string(),
            timeout_ms: Some(5000),
        };

        let creds = if config.api_key.is_some() && config.api_secret.is_some() {
            Some(Credential {
                api_key: config.api_key.unwrap(),
                api_secret: config.api_secret.unwrap(),
            })
        } else {
            None
        };

        let client = HttpClient::new(config.base_url, config.chain_id, creds);
        Ok(Self { client })
    }

    fn get_tickers<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        pyo3_asyncio::tokio::future_into_py(py, async move {
            let result = client.get::<Vec<Ticker>>("/v1/tickers", false).await;
            Python::with_gil(|py| {
                match result {
                    Ok(tickers) => {
                        let py_list: Vec<PyObject> = tickers.into_iter().map(|t| {
                            let dict = PyDict::new(py);
                            dict.set_item("symbol", t.symbol).unwrap();
                            dict.set_item("lastPrice", t.last_price).unwrap();
                            dict.set_item("volume", t.volume).unwrap();
                            dict.set_item("priceStep", t.price_step).unwrap();
                            dict.set_item("sizeStep", t.size_step).unwrap();
                            dict.into()
                        }).collect();
                        Ok(py_list)
                    },
                    Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
                }
            })
        })
    }
}