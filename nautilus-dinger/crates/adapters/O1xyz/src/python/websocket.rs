use pyo3::prelude::*;

/// Python bindings for the O1Xyz WebSocket client.
#[pyclass]
pub struct PyO1XyzWebSocketClient {
    url: String,
}

#[pymethods]
impl PyO1XyzWebSocketClient {
    #[new]
    pub fn new(url: Option<String>) -> Self {
        Self {
            url: url.unwrap_or_else(|| "wss://api.o1.exchange/ws".to_string()),
        }
    }

    pub fn get_url(&self) -> &str {
        &self.url
    }
}
