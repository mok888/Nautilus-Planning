use pyo3::prelude::*;

/// Python bindings for the Nado HTTP client.
#[pyclass]
pub struct PyNadoHttpClient {
    base_url: String,
}

#[pymethods]
impl PyNadoHttpClient {
    #[new]
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "https://gateway.prod.nado.xyz".to_string()),
        }
    }

    pub fn get_base_url(&self) -> &str {
        &self.base_url
    }
}
