use pyo3::prelude::*;

/// Python bindings for the Grvt WebSocket client.
#[pyclass]
pub struct PyGrvtWebSocketClient {
    url: String,
}

#[pymethods]
impl PyGrvtWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://trades.grvt.io/ws/full".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
