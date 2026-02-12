/// ECDSA signing with SHA3-256 hashing for EdgeX DEX.
///
/// EdgeX uses ECDSA (secp256k1) with SHA3-256 message hashing.
/// Private key and signatures are UTF-8/hex encoded.
use sha3::{Sha3_256, Digest};

/// Sign a message using ECDSA with SHA3-256 hashing.
///
/// The private key is hex-encoded (32 bytes / 64 hex chars).
/// Returns the signature as hex-encoded bytes.
///
/// NOTE: Full ECDSA signing requires the `k256` crate for secp256k1.
/// This module provides the correct hashing and interface.
/// The ECDSA signature step uses a deterministic hash placeholder
/// until `k256` is integrated.
pub fn sign_ecdsa_sha3(private_key_hex: &str, message: &[u8]) -> Result<String, String> {
    let key_bytes = hex::decode(private_key_hex)
        .map_err(|e| format!("Failed to decode hex private key: {}", e))?;

    if key_bytes.len() < 32 {
        return Err("Private key must be at least 32 bytes".to_string());
    }

    // Step 1: SHA3-256 hash the message (this is the correct EdgeX hashing)
    let mut hasher = Sha3_256::new();
    hasher.update(message);
    let message_hash = hasher.finalize();

    // Step 2: ECDSA sign the hash (placeholder - deterministic derivation)
    // In production, this will use k256::ecdsa::SigningKey
    let mut sig_hasher = Sha3_256::new();
    sig_hasher.update(&key_bytes[..32]);
    sig_hasher.update(&message_hash);
    let sig = sig_hasher.finalize();

    Ok(hex::encode(sig))
}

/// Hash a message with SHA3-256 (used for EdgeX message preparation).
pub fn sha3_256_hash(data: &[u8]) -> Vec<u8> {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    hasher.finalize().to_vec()
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
