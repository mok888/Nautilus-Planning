use pyo3::prelude::*;

/// Python bindings for the StandX WebSocket client.
#[pyclass]
pub struct PyStandXWebSocketClient {
    url: String,
}

#[pymethods]
impl PyStandXWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://perps.standx.com/ws-stream/v1".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
