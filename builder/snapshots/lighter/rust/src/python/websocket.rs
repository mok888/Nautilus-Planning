use pyo3::prelude::*;

/// Python bindings for the Lighter WebSocket client.
#[pyclass]
pub struct PyLighterWebSocketClient {
    url: String,
}

#[pymethods]
impl PyLighterWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://mainnet.zklighter.elliot.ai/stream".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
