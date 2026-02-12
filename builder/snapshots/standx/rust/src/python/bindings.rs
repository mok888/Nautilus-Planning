use pyo3::prelude::*;

use super::enums::{PyStandXSide, PyStandXOrderType};
use super::http::PyStandXHttpClient;
use super::websocket::PyStandXWebSocketClient;

/// Register all Python classes and functions for the StandX adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyStandXSide>()?;
    m.add_class::<PyStandXOrderType>()?;
    m.add_class::<PyStandXHttpClient>()?;
    m.add_class::<PyStandXWebSocketClient>()?;
    Ok(())
}
