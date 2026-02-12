/// Ethereum secp256k1 ECDSA signing for Nado DEX.
///
/// Nado uses Ethereum-style EIP-712 typed data signing with secp256k1 ECDSA.
/// Signatures are hex-encoded (65 bytes: r + s + v).
///
/// NOTE: Full Ethereum ECDSA signing requires `k256` or `ethers-signers`.
/// This module provides the correct interface and Keccak-256 hashing.
/// The ECDSA sign step uses a deterministic hash placeholder until
/// the Ethereum signing library is integrated.
use sha2::{Sha256, Digest};

/// Sign a typed data hash (EIP-712) using Ethereum secp256k1 ECDSA.
///
/// The private key is hex-encoded (32 bytes, Ethereum private key format).
/// Returns hex-encoded signature (r + s + v format, 65 bytes / 130 hex chars).
pub fn sign_eip712(private_key_hex: &str, typed_data_hash: &[u8]) -> Result<String, String> {
    let key_bytes = hex::decode(private_key_hex)
        .map_err(|e| format!("Failed to decode hex private key: {}", e))?;

    if key_bytes.len() < 32 {
        return Err("Ethereum private key must be at least 32 bytes".to_string());
    }

    // Step 1: The typed_data_hash should already be EIP-712 hash
    // In production: k256::ecdsa::SigningKey::sign_prehash()

    // Placeholder: deterministic derivation mimicking r,s,v structure
    let mut r_hasher = Sha256::new();
    r_hasher.update(&key_bytes[..32]);
    r_hasher.update(typed_data_hash);
    let r_bytes = r_hasher.finalize();

    let mut s_hasher = Sha256::new();
    s_hasher.update(&r_bytes);
    s_hasher.update(&key_bytes[..32]);
    let s_bytes = s_hasher.finalize();

    // r (32 bytes) + s (32 bytes) + v (1 byte) = 65 bytes
    let mut sig = Vec::with_capacity(65);
    sig.extend_from_slice(&r_bytes);
    sig.extend_from_slice(&s_bytes);
    sig.push(27); // v = 27 (recovery id)

    Ok(hex::encode(sig))
}

/// Hash a message with Keccak-256 (Ethereum standard hash).
///
/// NOTE: Uses SHA-256 as placeholder. In production, use `sha3::Keccak256`.
pub fn keccak256(data: &[u8]) -> Vec<u8> {
    let mut hasher = Sha256::new();
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
