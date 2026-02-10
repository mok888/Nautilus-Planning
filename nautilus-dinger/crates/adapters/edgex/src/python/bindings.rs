use pyo3::prelude::*;

/// Helper to register common bindings if needed
pub fn register(_m: &Bound<'_, PyModule>) -> PyResult<()> {
    Ok(())
}
