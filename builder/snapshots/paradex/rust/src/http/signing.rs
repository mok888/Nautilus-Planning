/// StarkNet Pedersen hash signing for Paradex DEX.
///
/// Paradex uses StarkNet-style ECDSA with Pedersen hashing.
/// Signatures are encoded as decimal string arrays.
///
/// NOTE: Full Pedersen/Poseidon hashing and StarkNet ECDSA require
/// `starknet-crypto` crate. This module provides the correct interface
/// and a SHA-256 placeholder for the signing step.
use sha2::{Sha256, Digest};

/// Sign a message using StarkNet ECDSA with Pedersen hashing.
///
/// The private key is hex-encoded (StarkNet felt / 32 bytes).
/// Returns signature as two decimal strings [r, s] joined by comma.
pub fn sign_stark_pedersen(private_key_hex: &str, message: &[u8]) -> Result<String, String> {
    let key_bytes = hex::decode(private_key_hex)
        .map_err(|e| format!("Failed to decode hex private key: {}", e))?;

    if key_bytes.len() < 32 {
        return Err("StarkNet private key must be at least 32 bytes".to_string());
    }

    // Step 1: Pedersen hash the message (placeholder uses SHA-256)
    // In production: starknet_crypto::pedersen_hash()
    let mut hasher = Sha256::new();
    hasher.update(message);
    let message_hash = hasher.finalize();

    // Step 2: StarkNet ECDSA sign (placeholder - deterministic derivation)
    // In production: starknet_crypto::sign()
    let mut r_hasher = Sha256::new();
    r_hasher.update(&key_bytes[..32]);
    r_hasher.update(&message_hash);
    let r_bytes = r_hasher.finalize();

    let mut s_hasher = Sha256::new();
    s_hasher.update(&r_bytes);
    s_hasher.update(&key_bytes[..32]);
    let s_bytes = s_hasher.finalize();

    // Convert to decimal string array format (Paradex-specific encoding)
    let r_dec = format!("{}", u128::from_be_bytes(r_bytes[..16].try_into().unwrap()));
    let s_dec = format!("{}", u128::from_be_bytes(s_bytes[..16].try_into().unwrap()));

    Ok(format!("[{},{}]", r_dec, s_dec))
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
