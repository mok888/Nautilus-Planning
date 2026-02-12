use pyo3::prelude::*;

use super::enums::{PyGrvtSide, PyGrvtOrderType};
use super::http::PyGrvtHttpClient;
use super::websocket::PyGrvtWebSocketClient;

/// Register all Python classes and functions for the Grvt adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyGrvtSide>()?;
    m.add_class::<PyGrvtOrderType>()?;
    m.add_class::<PyGrvtHttpClient>()?;
    m.add_class::<PyGrvtWebSocketClient>()?;
    Ok(())
}
