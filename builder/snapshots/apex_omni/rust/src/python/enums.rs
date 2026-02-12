use pyo3::prelude::*;

use crate::common::enums::{ApexOmniSide, ApexOmniOrderType};

/// Expose ApexOmni enums to Python via PyO3.
#[pyclass]
#[derive(Clone)]
pub struct PyApexOmniSide {
    inner: ApexOmniSide,
}

#[pymethods]
impl PyApexOmniSide {
    #[staticmethod]
    pub fn buy() -> Self {
        Self { inner: ApexOmniSide::Buy }
    }

    #[staticmethod]
    pub fn sell() -> Self {
        Self { inner: ApexOmniSide::Sell }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct PyApexOmniOrderType {
    inner: ApexOmniOrderType,
}

#[pymethods]
impl PyApexOmniOrderType {
    #[staticmethod]
    pub fn limit() -> Self {
        Self { inner: ApexOmniOrderType::Limit }
    }

    #[staticmethod]
    pub fn market() -> Self {
        Self { inner: ApexOmniOrderType::Market }
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}
