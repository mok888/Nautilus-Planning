use pyo3::prelude::*;

/// Python bindings for the Edgex WebSocket client.
#[pyclass]
pub struct PyEdgexWebSocketClient {
    url: String,
}

#[pymethods]
impl PyEdgexWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://quote.edgex.exchange".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
