/// SHA-256 wallet-based signing for Apex Omni DEX.
///
/// Apex Omni uses a wallet-based auth flow with SHA-256 message hashing
/// and hex-encoded signatures.
use sha2::{Sha256, Digest};

/// Sign a message using SHA-256 wallet signing.
///
/// The private key is hex-encoded. The message is SHA-256 hashed,
/// then signed with the wallet key. Returns hex-encoded signature.
///
/// NOTE: Apex Omni's actual wallet signing may use a specific
/// ZK proof system or L2-specific signing. This provides the
/// SHA-256 hashing interface that Apex Omni's API expects.
pub fn sign_wallet_sha256(private_key_hex: &str, message: &[u8]) -> Result<String, String> {
    let key_bytes = hex::decode(private_key_hex)
        .map_err(|e| format!("Failed to decode hex private key: {}", e))?;

    if key_bytes.len() < 32 {
        return Err("Wallet private key must be at least 32 bytes".to_string());
    }

    // Step 1: SHA-256 hash the message
    let mut hasher = Sha256::new();
    hasher.update(message);
    let message_hash = hasher.finalize();

    // Step 2: Sign with wallet key (deterministic derivation placeholder)
    // In production, this will use the specific ZK/wallet signing scheme
    let mut sig_hasher = Sha256::new();
    sig_hasher.update(&key_bytes[..32]);
    sig_hasher.update(&message_hash);
    let sig = sig_hasher.finalize();

    Ok(hex::encode(sig))
}

/// Hash a message with SHA-256.
pub fn sha256_hash(data: &[u8]) -> Vec<u8> {
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
