use pyo3::prelude::*;

use crate::common::enums::{StandXOrderType, StandXSide};

/// Expose StandX enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyStandXSide {
    inner: StandXSide,
}

#[pymethods]
impl PyStandXSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: StandXSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: StandXSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyStandXOrderType {
    inner: StandXOrderType,
}

#[pymethods]
impl PyStandXOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: StandXOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: StandXOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
