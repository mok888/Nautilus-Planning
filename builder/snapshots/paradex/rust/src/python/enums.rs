use pyo3::prelude::*;

use crate::common::enums::{ParadexSide, ParadexOrderType};

/// Expose Paradex enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyParadexSide {
    inner: ParadexSide,
}

#[pymethods]
impl PyParadexSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: ParadexSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: ParadexSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyParadexOrderType {
    inner: ParadexOrderType,
}

#[pymethods]
impl PyParadexOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: ParadexOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: ParadexOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
