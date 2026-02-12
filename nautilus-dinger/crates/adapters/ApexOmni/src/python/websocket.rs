use pyo3::prelude::*;

/// Python bindings for the ApexOmni WebSocket client.
#[pyclass]
pub struct PyApexOmniWebSocketClient {
    url: String,
}

#[pymethods]
impl PyApexOmniWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://omni.apex.exchange/ws/v3".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
