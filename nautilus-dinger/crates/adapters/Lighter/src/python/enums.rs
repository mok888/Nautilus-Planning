use pyo3::prelude::*;

use crate::common::enums::{LighterOrderType, LighterSide};

/// Expose Lighter enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyLighterSide {
    inner: LighterSide,
}

#[pymethods]
impl PyLighterSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: LighterSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: LighterSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyLighterOrderType {
    inner: LighterOrderType,
}

#[pymethods]
impl PyLighterOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: LighterOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: LighterOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
