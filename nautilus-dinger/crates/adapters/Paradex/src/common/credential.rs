use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexCredential {
    pub starknet_private_key: String, // L2 Private Key (hex)
    pub starknet_account_address: String, // L2 Account Address (hex)
}

impl ParadexCredential {
    /// Resolve credentials from provided values or environment variables.
    pub fn resolve(
        starknet_private_key: Option<String>,
        starknet_account_address: Option<String>,
    ) -> Result<Option<Self>, String> {
        let starknet_private = get_or_env_var_opt(starknet_private_key, "PARADEX_STARKNET_PRIVATE_KEY");
        let starknet_account = get_or_env_var_opt(starknet_account_address, "PARADEX_STARKNET_ACCOUNT");

        match (starknet_private, starknet_account) {
            (Some(pk), Some(addr)) => Ok(Some(Self {
                starknet_private_key: pk,
                starknet_account_address: addr,
            })),
            _ => Ok(None),
        }
    }

    /// Derive the public key hex from the private key.
    /// Uses starknet_crypto to get the public key from the private key.
    pub fn public_key_hex(&self) -> Result<String, String> {
        use starknet_ff::FieldElement;
        // Get public key from private key using the KeyPair approach
        let pk = FieldElement::from_hex_be(&self.starknet_private_key)
            .map_err(|e| format!("Invalid private key hex: {}", e))?;
        let public_key = starknet_crypto::get_public_key(&pk);
        Ok(format!("{:#x}", public_key))
    }
}

fn get_or_env_var_opt(value: Option<String>, env_key: &str) -> Option<String> {
    value.or_else(|| env::var(env_key).ok())
}
