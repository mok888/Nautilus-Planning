use pyo3::prelude::*;

use crate::common::enums::{EdgexSide, EdgexOrderType};

/// Expose Edgex enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyEdgexSide {
    inner: EdgexSide,
}

#[pymethods]
impl PyEdgexSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: EdgexSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: EdgexSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyEdgexOrderType {
    inner: EdgexOrderType,
}

#[pymethods]
impl PyEdgexOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: EdgexOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: EdgexOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
