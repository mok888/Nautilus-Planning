use pyo3::prelude::*;

/// Python bindings for the ApexOmni HTTP client.
#[pyclass]
pub struct PyApexOmniHttpClient {
    base_url: String,
}

#[pymethods]
impl PyApexOmniHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://omni.apex.exchange/api".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
