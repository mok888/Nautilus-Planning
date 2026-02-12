use pyo3::prelude::*;

/// Python bindings for the Lighter HTTP client.
#[pyclass]
pub struct PyLighterHttpClient {
    base_url: String,
}

#[pymethods]
impl PyLighterHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://mainnet.zklighter.elliot.ai".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
