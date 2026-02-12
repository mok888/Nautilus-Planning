use pyo3::prelude::*;

/// Python bindings for the Nado WebSocket client.
#[pyclass]
pub struct PyNadoWebSocketClient {
    url: String,
}

#[pymethods]
impl PyNadoWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://gateway.prod.nado.xyz/ws".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
