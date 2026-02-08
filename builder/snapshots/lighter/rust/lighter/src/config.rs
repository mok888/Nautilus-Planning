// Copyright (C) 2024 Nautilus Technologies, Inc.
// SPDX-License-Identifier: MIT

use serde::{Deserialize, Serialize};
use nautilus_core::python::ToPyResult;
use nautilus_model::identifiers::venue::Venue;
use pyo3::{prelude::*, types::PyDict};

/// Represents the configuration for the Lighter DEX adapter.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(crate = "serde")]
pub struct LighterConfig {
    /// The API key for authentication.
    pub api_key: String,
    /// The secret key for signing requests.
    pub api_secret: String,
    /// The chain ID (e.g., 137 for Polygon).
    pub chain_id: String,
    /// Optional: Explicit base URL override.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub base_url: Option<String>,
}

impl LighterConfig {
    pub const VENUE: Venue = Venue::from("LIGHTER");
    pub const DEFAULT_BASE_URL: &str = "https://api.lighter.xyz";
    pub const DEFAULT_WS_URL: &str = "wss://api.lighter.xyz/ws";

    pub fn new(api_key: String, api_secret: String, chain_id: String) -> Self {
        Self {
            api_key,
            api_secret,
            chain_id,
            base_url: None,
        }
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl LighterConfig {
    #[new]
    #[pyo3(signature = (api_key, api_secret, chain_id, base_url=None))]
    fn py_new(api_key: String, api_secret: String, chain_id: String, base_url: Option<String>) -> PyResult<Self> {
        Ok(Self {
            api_key,
            api_secret,
            chain_id,
            base_url,
        })
    }

    #[staticmethod]
    #[pyo3(name = "from_dict")]
    fn py_from_dict(config: &PyDict) -> PyResult<Self> {
        let api_key = config.get_item("api_key")?.unwrap().extract()?;
        let api_secret = config.get_item("api_secret")?.unwrap().extract()?;
        let chain_id = config.get_item("chain_id")?.unwrap().extract()?;
        let base_url = config.get_item("base_url")?.map(|v| v.extract()).transpose()?;
        Ok(Self { api_key, api_secret, chain_id, base_url })
    }

    fn __repr__(&self) -> String {
        format!("LighterConfig(api_key='***', chain_id='{}')", self.chain_id)
    }
}
