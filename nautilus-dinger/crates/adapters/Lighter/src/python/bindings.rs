use pyo3::prelude::*;

use super::enums::{PyLighterOrderType, PyLighterSide};
use super::http::{PyLighterHttpClient, PyLighterRawHttpClient};
use super::websocket::PyLighterWebSocketClient;

/// Register all Python classes and functions for the Lighter adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLighterSide>()?;
    m.add_class::<PyLighterOrderType>()?;
    m.add_class::<PyLighterRawHttpClient>()?;
    m.add_class::<PyLighterHttpClient>()?;
    m.add_class::<PyLighterWebSocketClient>()?;
    Ok(())
}
