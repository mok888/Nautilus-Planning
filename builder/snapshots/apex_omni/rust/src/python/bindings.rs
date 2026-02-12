use pyo3::prelude::*;

use super::enums::{PyApexOmniSide, PyApexOmniOrderType};
use super::http::PyApexOmniHttpClient;
use super::websocket::PyApexOmniWebSocketClient;

/// Register all Python classes and functions for the ApexOmni adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyApexOmniSide>()?;
    m.add_class::<PyApexOmniOrderType>()?;
    m.add_class::<PyApexOmniHttpClient>()?;
    m.add_class::<PyApexOmniWebSocketClient>()?;
    Ok(())
}
