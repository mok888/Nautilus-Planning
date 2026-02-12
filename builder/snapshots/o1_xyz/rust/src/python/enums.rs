use pyo3::prelude::*;

use crate::common::enums::{O1XyzSide, O1XyzOrderType};

/// Expose O1Xyz enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyO1XyzSide {
    inner: O1XyzSide,
}

#[pymethods]
impl PyO1XyzSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: O1XyzSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: O1XyzSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyO1XyzOrderType {
    inner: O1XyzOrderType,
}

#[pymethods]
impl PyO1XyzOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: O1XyzOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: O1XyzOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
