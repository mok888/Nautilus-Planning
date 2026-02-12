use pyo3::prelude::*;

/// Python bindings for the Paradex WebSocket client.
#[pyclass]
pub struct PyParadexWebSocketClient {
    url: String,
}

#[pymethods]
impl PyParadexWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://ws.api.prod.paradex.trade/v1".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
