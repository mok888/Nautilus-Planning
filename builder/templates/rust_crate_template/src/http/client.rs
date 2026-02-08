use std::sync::Arc;
use nautilus_network::http::HttpClient;
use nautilus_common::live::get_runtime;
use crate::common::credential::{{EXCHANGE_NAME}}Credential;
use anyhow;

/// Raw client matching venue API endpoints.
pub struct {{EXCHANGE_NAME}}RawHttpClient {
    base_url: String,
    client: HttpClient,
}

/// Domain client exposing Nautilus types.
pub struct {{EXCHANGE_NAME}}HttpClient {
    inner: Arc<{{EXCHANGE_NAME}}RawHttpClient>,
    // Add DashMap for instrument cache here if needed
}

impl {{EXCHANGE_NAME}}HttpClient {
    pub fn new(base_url: String, client: HttpClient) -> Self {
        Self {
            inner: Arc::new({{EXCHANGE_NAME}}RawHttpClient { base_url, client }),
        }
    }

    pub fn request_something(&self) -> anyhow::Result<String> {
        // Enforce global runtime usage for blocking calls
        let inner = self.inner.clone();
        get_runtime().block_on(async move {
            // async logic using inner.client
            Ok("response".to_string())
        })
    }
}
