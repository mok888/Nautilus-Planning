//! NautilusTrader Adapter - Lighter Signing Logic

use crate::config::LighterConfig;
use crate::error::{LighterError, Result};
use hex::ToHex;
use hmac::{Hmac, Mac};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

/// Generates the X-Signature header value.
/// Payload format: timestamp + method + requestPath + body
pub fn generate_signature(
    config: &LighterConfig,
    timestamp: u64,
    method: &str,
    path: &str,
    body: &str,
) -> Result<String> {
    let secret = config
        .api_secret
        .as_ref()
        .ok_or_else(|| LighterError::AuthError("API Secret missing".to_string()))?;

    // Construct payload: timestamp + method + requestPath + body
    let payload = format!("{}{}{}{}", timestamp, method, path, body);

    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
        .map_err(|e| LighterError::AuthError(format!("HMAC Error: {}", e)))?;
    mac.update(payload.as_bytes());

    Ok(mac.finalize().into_bytes().encode_hex())
}