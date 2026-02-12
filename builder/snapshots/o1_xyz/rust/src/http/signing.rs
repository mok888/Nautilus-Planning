use ed25519_dalek::{Signer, SigningKey};

/// Sign a message using Solana Ed25519 (ed25519-dalek).
///
/// The secret key is expected to be a 64-byte base58-encoded Solana keypair
/// (first 32 bytes are the private key, last 32 bytes are the public key).
pub fn sign_ed25519(secret_base58: &str, message: &[u8]) -> Result<Vec<u8>, String> {
    let keypair_bytes = bs58::decode(secret_base58)
        .into_vec()
        .map_err(|e| format!("Failed to decode base58 secret key: {}", e))?;

    if keypair_bytes.len() < 32 {
        return Err("Secret key must be at least 32 bytes".to_string());
    }

    let secret_bytes: [u8; 32] = keypair_bytes[..32]
        .try_into()
        .map_err(|_| "Failed to extract 32-byte secret key".to_string())?;

    let signing_key = SigningKey::from_bytes(&secret_bytes);
    let signature = signing_key.sign(message);

    Ok(signature.to_bytes().to_vec())
}

/// Sign a message and return the signature as a base58 string.
pub fn sign_ed25519_base58(secret_base58: &str, message: &[u8]) -> Result<String, String> {
    let sig_bytes = sign_ed25519(secret_base58, message)?;
    Ok(bs58::encode(sig_bytes).into_string())
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
