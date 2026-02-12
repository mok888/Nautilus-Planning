use pyo3::prelude::*;

use super::enums::{PyNadoSide, PyNadoOrderType};
use super::http::PyNadoHttpClient;
use super::websocket::PyNadoWebSocketClient;

/// Register all Python classes and functions for the Nado adapter.
pub fn register_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyNadoSide>()?;
    m.add_class::<PyNadoOrderType>()?;
    m.add_class::<PyNadoHttpClient>()?;
    m.add_class::<PyNadoWebSocketClient>()?;
    Ok(())
}
