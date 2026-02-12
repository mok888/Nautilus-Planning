use pyo3::prelude::*;

use super::enums::{PyO1XyzSide, PyO1XyzOrderType};
use super::http::PyO1XyzHttpClient;
use super::websocket::PyO1XyzWebSocketClient;

/// Register all Python classes and functions for the O1Xyz adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyO1XyzSide>()?;
    m.add_class::<PyO1XyzOrderType>()?;
    m.add_class::<PyO1XyzHttpClient>()?;
    m.add_class::<PyO1XyzWebSocketClient>()?;
    Ok(())
}
