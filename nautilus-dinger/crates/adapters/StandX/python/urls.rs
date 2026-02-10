use pyo3::prelude::*;
use crate::common::urls;

#[pyfunction]
pub fn get_rest_base_url() -> &'static str {
    urls::REST_BASE_URL
}

#[pyfunction]
pub fn get_ws_public_url() -> &'static str {
    urls::WS_PUBLIC_URL
}

#[pyfunction]
pub fn get_ws_private_url() -> &'static str {
    urls::WS_PRIVATE_URL
}
