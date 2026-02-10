use pyo3::prelude::*;

#[pyfunction]
pub fn get_rest_url() -> PyResult<String> {
    Ok("https://pro.edgex.exchange".to_string())
}
