use crate::config::LighterConfig;
use crate::error::Result;
use chrono::Utc;
use hmac::{Hmac, Mac};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

pub fn generate_signature(
    config: &LighterConfig,
    method: &str,
    path: &str,
    body: &str,
) -> Result<(String, String)> {
    let timestamp = Utc::now().timestamp_millis().to_string();
    
    // Construct payload: timestamp + method + requestPath + body
    let payload = format!("{}{}{}{}", timestamp, method, path, body);
    
    let mut mac = HmacSha256::new_from_slice(config.secret_key.as_bytes())
        .map_err(|e| crate::error::LighterError::Signing(e.to_string()))?;
    
    mac.update(payload.as_bytes());
    let signature = hex::encode(mac.finalize().into_bytes());
    
    Ok((timestamp, signature))
}