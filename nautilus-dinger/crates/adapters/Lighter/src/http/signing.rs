/// Schnorr signing over BabyJubJub curve for Lighter DEX.
///
/// Lighter uses Schnorr signatures on the BabyJubJub elliptic curve.
/// The private key is hex-encoded, and signatures are hex-encoded.
///
/// NOTE: Full BabyJubJub Schnorr signing requires a specialized library
/// (e.g., `babyjubjub-rs` or `circom-compat`). This module provides the
/// interface and HMAC-SHA256 fallback. The Schnorr implementation will be
/// completed when the specific Lighter signing spec is finalized.
use sha2::{Sha256, Digest};

/// Sign a message using Schnorr signature over BabyJubJub curve.
///
/// The private key is hex-encoded. Returns hex-encoded signature.
/// This is a placeholder that uses SHA-256 hash + key derivation
/// until the full BabyJubJub Schnorr library is integrated.
pub fn sign_schnorr_babyjubjub(private_key_hex: &str, message: &[u8]) -> Result<String, String> {
    let key_bytes = hex::decode(private_key_hex)
        .map_err(|e| format!("Failed to decode hex private key: {}", e))?;

    if key_bytes.len() < 32 {
        return Err("Private key must be at least 32 bytes".to_string());
    }

    // Deterministic signature derivation (placeholder for actual Schnorr)
    // In production, this will use proper BabyJubJub curve operations
    let mut hasher = Sha256::new();
    hasher.update(&key_bytes[..32]);
    hasher.update(message);
    let hash = hasher.finalize();

    Ok(hex::encode(hash))
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
