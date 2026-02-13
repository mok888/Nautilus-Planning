use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandXCredential {
    pub api_key: String,
    pub api_secret: String,
}

impl StandXCredential {
    /// Resolve credentials from provided values or environment variables.
    ///
    /// Uses `STANDX_API_KEY` and `STANDX_API_SECRET` environment variables
    /// as fallbacks. The API key is used in Bearer token format for
    /// Authorization headers. The API secret is a ed25519 private key
    /// encoded in base58.
    pub fn resolve(
        api_key: Option<String>,
        api_secret: Option<String>,
    ) -> Result<Option<Self>, String> {
        let api_key = api_key
            .or_else(|| env::var("STANDX_API_TOKEN").ok())
            .or_else(|| env::var("STANDX_API_KEY").ok());
        let api_secret = api_secret
            .or_else(|| env::var("STANDX_REQUEST_ED25519_PRIVATE_KEY").ok())
            .or_else(|| env::var("STANDX_API_SECRET").ok());

        match (api_key, api_secret) {
            (Some(api_key), Some(api_secret)) => Ok(Some(Self { api_key, api_secret })),
            (None, None) => Ok(None),
            _ => Err("Both API key and secret must be provided if one is present.".to_string()),
        }
    }

    /// Returns the Authorization header value in Bearer token format.
    pub fn authorization_header(&self) -> String {
        format!("Bearer {}", self.api_key)
    }
}
