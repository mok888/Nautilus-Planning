//! NautilusTrader Adapter - Python URL Helpers

use pyo3::prelude::*;

#[pyfunction]
pub fn get_rest_base_url() -> String {
    crate::common::urls::REST_BASE_URL.to_string()
}

#[pyfunction]
pub fn get_ws_base_url() -> String {
    crate::common::urls::WS_BASE_URL.to_string()
}

#[pymodule]
fn _lighter_urls(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_rest_base_url, m)?)?;
    m.add_function(wrap_pyfunction!(get_ws_base_url, m)?)?;
    Ok(())
}