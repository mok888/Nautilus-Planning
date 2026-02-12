use pyo3::prelude::*;

/// Python bindings for the StandX HTTP client.
#[pyclass]
pub struct PyStandXHttpClient {
    base_url: String,
}

#[pymethods]
impl PyStandXHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://perps.standx.com".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
