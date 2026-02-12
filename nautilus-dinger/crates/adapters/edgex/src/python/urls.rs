use pyo3::prelude::*;

#[pyfunction]
pub fn get_rest_url(sandbox: Option<bool>) -> PyResult<String> {
    let sandbox = sandbox.unwrap_or(false);
    Ok(crate::common::urls::get_rest_url(sandbox))
}

#[pyfunction]
pub fn get_ws_url(sandbox: Option<bool>) -> PyResult<String> {
    let sandbox = sandbox.unwrap_or(false);
    Ok(crate::common::urls::get_ws_url(sandbox))
}
