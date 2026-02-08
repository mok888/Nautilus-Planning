pub mod common;
pub mod config;
pub mod error;
pub mod http;
pub mod websocket;

#[cfg(feature = "python")]
pub mod python;

#[cfg(feature = "data")]
pub mod data;

#[cfg(feature = "execution")]
pub mod execution;

#[cfg(any(test, feature = "test_utils"))]
pub mod testing;

use pyo3::prelude::*;

#[pymodule]
fn lighter(_py: Python, m: &PyModule) -> PyResult<()> {
    #[cfg(feature = "python")]
    python::register_modules(_py, m)?;
    Ok(())
}
