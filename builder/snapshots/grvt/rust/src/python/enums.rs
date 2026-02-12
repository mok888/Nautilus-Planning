use pyo3::prelude::*;

use crate::common::enums::{GrvtSide, GrvtOrderType};

/// Expose Grvt enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyGrvtSide {
    inner: GrvtSide,
}

#[pymethods]
impl PyGrvtSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: GrvtSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: GrvtSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyGrvtOrderType {
    inner: GrvtOrderType,
}

#[pymethods]
impl PyGrvtOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: GrvtOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: GrvtOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
