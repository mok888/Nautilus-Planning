use pyo3::prelude::*;

use super::enums::{PyEdgexSide, PyEdgexOrderType};
use super::http::PyEdgexHttpClient;
use super::websocket::PyEdgexWebSocketClient;

/// Register all Python classes and functions for the Edgex adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyEdgexSide>()?;
    m.add_class::<PyEdgexOrderType>()?;
    m.add_class::<PyEdgexHttpClient>()?;
    m.add_class::<PyEdgexWebSocketClient>()?;
    Ok(())
}
