use crate::error::Result;
use hmac::{Hmac, Mac};
use sha2::Sha256;
use std::time::{SystemTime, UNIX_EPOCH};

type HmacSha256 = Hmac<Sha256>;

pub fn generate_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("Time went backwards")
        .as_millis() as u64
}

pub struct Signer {
    api_secret: String,
}

impl Signer {
    pub fn new(api_secret: String) -> Self {
        Self { api_secret }
    }

    /// Signature payload: timestamp + method + requestPath + body
    pub fn sign(&self, timestamp: u64, method: &str, path: &str, body: &str) -> Result<String> {
        let payload = format!("{}{}{}{}", timestamp, method, path, body);
        
        let mut mac = HmacSha256::new_from_slice(self.api_secret.as_bytes())
            .map_err(|_| crate::error::LighterAdapterError::InvalidCredentials)?;
        mac.update(payload.as_bytes());
        
        let result = mac.finalize();
        let code_bytes = result.into_bytes();
        
        Ok(hex::encode(code_bytes))
    }
}