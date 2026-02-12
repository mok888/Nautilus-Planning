use pyo3::prelude::*;

use super::enums::{PyParadexSide, PyParadexOrderType};
use super::http::PyParadexHttpClient;
use super::websocket::PyParadexWebSocketClient;

/// Register all Python classes and functions for the Paradex adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyParadexSide>()?;
    m.add_class::<PyParadexOrderType>()?;
    m.add_class::<PyParadexHttpClient>()?;
    m.add_class::<PyParadexWebSocketClient>()?;
    Ok(())
}
