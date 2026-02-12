use pyo3::prelude::*;

/// Python bindings for the Grvt HTTP client.
#[pyclass]
pub struct PyGrvtHttpClient {
    base_url: String,
}

#[pymethods]
impl PyGrvtHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://edge.grvt.io".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
