use pyo3::prelude::*;

use super::enums::{PyLighterSide, PyLighterOrderType};
use super::http::PyLighterHttpClient;
use super::websocket::PyLighterWebSocketClient;

/// Register all Python classes and functions for the Lighter adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLighterSide>()?;
    m.add_class::<PyLighterOrderType>()?;
    m.add_class::<PyLighterHttpClient>()?;
    m.add_class::<PyLighterWebSocketClient>()?;
    Ok(())
}
