use pyo3::prelude::*;

#[pyfunction]
pub fn get_rest_url() -> PyResult<String> {
    Ok("{{REST_URL_MAINNET}}".to_string())
}
