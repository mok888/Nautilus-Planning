use pyo3::prelude::*;

use crate::common::enums::{NadoSide, NadoOrderType};

/// Expose Nado enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyNadoSide {
    inner: NadoSide,
}

#[pymethods]
impl PyNadoSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: NadoSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: NadoSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyNadoOrderType {
    inner: NadoOrderType,
}

#[pymethods]
impl PyNadoOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: NadoOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: NadoOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
