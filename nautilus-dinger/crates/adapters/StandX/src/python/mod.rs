pub mod bindings;
pub mod enums;
pub mod http;
pub mod urls;
pub mod websocket;

use pyo3::prelude::*;

pub fn register_modules(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(urls::get_rest_url, parent_module)?)?;
    parent_module.add_function(wrap_pyfunction!(urls::get_ws_url, parent_module)?)?;
    bindings::register_bindings(parent_module)?;
    Ok(())
}
