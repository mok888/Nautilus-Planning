use pyo3::prelude::*;

#[pyfunction]
pub fn get_server_time() -> PyResult<u64> {
    Ok(1234567890)
}
