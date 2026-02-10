use crate::error::StandXError;
use ed25519_dalek::{Signer, SigningKey, VerifyingKey};
use sha2::Sha512;
use base64::{Engine as _, engine::general_purpose};

/// StandX Request Signer using Ed25519
pub struct StandXSigner {
    secret: String,
}

impl StandXSigner {
    pub fn new(secret: String) -> Self {
        Self { secret }
    }

    /// Signs the request payload according to spec: {version},{id},{timestamp},{payload}
    /// Algorithm: Ed25519
    pub fn sign(
        &self,
        version: &str,
        id: &str,
        timestamp: &str,
        payload: &str,
    ) -> Result<String, StandXError> {
        // Construct payload string
        let payload_str = format!("{},{},{},{}", version, id, timestamp, payload);
        
        // Decode secret (Assuming API secret is the base64 encoded private key or hex, 
        // StandX docs usually imply the secret is the private key material)
        // For this implementation, we assume the secret is the hex string of the seed.
        let key_bytes = hex::decode(&self.secret)
            .map_err(|e| StandXError::SignatureError(format!("Invalid secret hex: {}", e)))?;
        
        let signing_key = SigningKey::from_bytes(&key_bytes);
        
        // Sign
        let signature = signing_key.sign(payload_str.as_bytes());
        
        // Encode to Base64
        Ok(general_purpose::STANDARD.encode(signature.to_bytes()))
    }
}
