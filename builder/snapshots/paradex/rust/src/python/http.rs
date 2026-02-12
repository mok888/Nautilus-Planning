use pyo3::prelude::*;

/// Python bindings for the Paradex HTTP client.
#[pyclass]
pub struct PyParadexHttpClient {
    base_url: String,
}

#[pymethods]
impl PyParadexHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://api.prod.paradex.trade/v1".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
