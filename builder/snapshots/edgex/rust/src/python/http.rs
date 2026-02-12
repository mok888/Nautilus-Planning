use pyo3::prelude::*;

/// Python bindings for the Edgex HTTP client.
#[pyclass]
pub struct PyEdgexHttpClient {
    base_url: String,
}

#[pymethods]
impl PyEdgexHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://pro.edgex.exchange".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
