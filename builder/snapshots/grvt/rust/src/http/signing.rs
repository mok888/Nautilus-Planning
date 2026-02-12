use ed25519_dalek::{Signer, SigningKey};

/// Sign a message using Ed25519 and return the signature as hex-encoded string.
///
/// GRVT uses Ed25519 with hex encoding for API request signing.
/// The secret key is a 32-byte key, provided as hex.
pub fn sign_ed25519_hex(secret_hex: &str, message: &[u8]) -> Result<String, String> {
    let key_bytes = hex::decode(secret_hex)
        .map_err(|e| format!("Failed to decode hex secret key: {}", e))?;

    if key_bytes.len() < 32 {
        return Err("Ed25519 secret key must be at least 32 bytes".to_string());
    }

    let secret_bytes: [u8; 32] = key_bytes[..32]
        .try_into()
        .map_err(|_| "Failed to extract 32-byte Ed25519 key".to_string())?;

    let signing_key = SigningKey::from_bytes(&secret_bytes);
    let signature = signing_key.sign(message);

    Ok(hex::encode(signature.to_bytes()))
}

/// Sign a raw message using Ed25519 and return the signature bytes.
pub fn sign_ed25519(secret_hex: &str, message: &[u8]) -> Result<Vec<u8>, String> {
    let key_bytes = hex::decode(secret_hex)
        .map_err(|e| format!("Failed to decode hex secret key: {}", e))?;

    if key_bytes.len() < 32 {
        return Err("Ed25519 secret key must be at least 32 bytes".to_string());
    }

    let secret_bytes: [u8; 32] = key_bytes[..32]
        .try_into()
        .map_err(|_| "Failed to extract 32-byte Ed25519 key".to_string())?;

    let signing_key = SigningKey::from_bytes(&secret_bytes);
    let signature = signing_key.sign(message);

    Ok(signature.to_bytes().to_vec())
}

/// Sign a message using HMAC-SHA256 (fallback for standard API key auth).
pub fn sign_hmac_sha256(secret: &str, message: &str) -> String {
    use hmac::{Hmac, Mac};
    use sha2::Sha256;

    type HmacSha256 = Hmac<Sha256>;

    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
        .expect("HMAC can take key of any size");
    mac.update(message.as_bytes());
    let result = mac.finalize();
    hex::encode(result.into_bytes())
}
