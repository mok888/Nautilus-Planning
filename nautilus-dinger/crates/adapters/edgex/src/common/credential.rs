use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct edgexCredential {
    pub api_key: String,
    pub api_secret: String,
}

impl edgexCredential {
    /// Resolve credentials from environment variables or configuration.
    pub fn resolve(
        api_key: Option<String>,
        api_secret: Option<String>,
    ) -> Result<Option<Self>, String> {
        let api_key = get_or_env_var_opt(api_key, "EDGEX_API_KEY");
        let api_secret = get_or_env_var_opt(api_secret, "EDGEX_API_SECRET");

        match (api_key, api_secret) {
            (Some(api_key), Some(api_secret)) => Ok(Some(Self {
                api_key,
                api_secret,
            })),
            (None, None) => Ok(None),
            _ => Err("Both API key and secret must be provided if one is present.".to_string()),
        }
    }
}

fn get_or_env_var_opt(value: Option<String>, env_key: &str) -> Option<String> {
    value.or_else(|| env::var(env_key).ok())
}
