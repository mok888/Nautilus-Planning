use pyo3::prelude::*;

/// Python bindings for the O1Xyz HTTP client.
#[pyclass]
pub struct PyO1XyzHttpClient {
    base_url: String,
}

#[pymethods]
impl PyO1XyzHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://zo-mainnet.n1.xyz".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
