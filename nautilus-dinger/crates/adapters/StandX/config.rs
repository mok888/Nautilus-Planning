use pyo3::prelude::*;
use crate::common::urls::{REST_BASE_URL, WS_PUBLIC_URL, WS_PRIVATE_URL};

#[pyclass]
#[derive(Clone, Debug, Default)]
pub struct StandXConfig {
    #[pyo3(get, set)]
    pub api_key: Option<String>,

    #[pyo3(get, set)]
    pub secret: Option<String>,

    #[pyo3(get, set)]
    pub rest_url: Option<String>,

    #[pyo3(get, set)]
    pub ws_public_url: Option<String>,

    #[pyo3(get, set)]
    pub ws_private_url: Option<String>,
}

#[pymethods]
impl StandXConfig {
    #[new]
    #[pyo3(signature = (api_key=None, secret=None, rest_url=None, ws_public_url=None, ws_private_url=None))]
    pub fn new(
        api_key: Option<String>,
        secret: Option<String>,
        rest_url: Option<String>,
        ws_public_url: Option<String>,
        ws_private_url: Option<String>,
    ) -> Self {
        Self {
            api_key,
            secret,
            rest_url,
            ws_public_url,
            ws_private_url,
        }
    }

    pub fn get_rest_url(&self) -> String {
        self.rest_url.clone().unwrap_or_else(|| REST_BASE_URL.to_string())
    }

    pub fn get_ws_public_url(&self) -> String {
        self.ws_public_url.clone().unwrap_or_else(|| WS_PUBLIC_URL.to_string())
    }

    pub fn get_ws_private_url(&self) -> String {
        self.ws_private_url.clone().unwrap_or_else(|| WS_PRIVATE_URL.to_string())
    }
}
