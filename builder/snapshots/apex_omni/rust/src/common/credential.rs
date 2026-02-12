use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApexOmniCredential {
    pub api_key: String,
    pub api_secret: String,
}

impl ApexOmniCredential {
    /// Resolve credentials from provided values or environment variables.
    ///
    /// Uses `APEX_OMNI_API_KEY` and `APEX_OMNI_API_SECRET` environment variables
    /// as fallbacks. The API key is used in Bearer token format for
    /// Authorization headers. The API secret is a zk_stark private key
    /// encoded in base58.
    pub fn resolve(
        api_key: Option<String>,
        api_secret: Option<String>,
    ) -> Result<Option<Self>, String> {
        let api_key = get_or_env_var_opt(api_key, "APEX_OMNI_API_KEY");
        let api_secret = get_or_env_var_opt(api_secret, "APEX_OMNI_API_SECRET");

        match (api_key, api_secret) {
            (Some(api_key), Some(api_secret)) => Ok(Some(Self {
                api_key,
                api_secret,
            })),
            (None, None) => Ok(None),
            _ => Err("Both API key and secret must be provided if one is present.".to_string()),
        }
    }

    /// Returns the Authorization header value in Bearer token format.
    pub fn authorization_header(&self) -> String {
        format!("Bearer {}", self.api_key)
    }
}

fn get_or_env_var_opt(value: Option<String>, env_key: &str) -> Option<String> {
    value.or_else(|| env::var(env_key).ok())
}
