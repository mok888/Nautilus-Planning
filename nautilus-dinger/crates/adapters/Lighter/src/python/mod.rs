pub mod enums;
pub mod http;
pub mod urls;
pub mod websocket;
pub mod bindings;

use pyo3::prelude::*;

pub fn register_modules(_py: Python, parent_module: &PyModule) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(urls::get_rest_url, parent_module)?)?;
    Ok(())
}
