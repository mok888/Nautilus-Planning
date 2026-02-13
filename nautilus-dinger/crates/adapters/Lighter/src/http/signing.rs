use dusk_bls12_381::BlsScalar;
use dusk_bytes::Serializable;
use jubjub_schnorr::{SecretKey, Signature};
use rand::rngs::StdRng;
use rand::SeedableRng;
use sha2::{Digest, Sha256};

fn message_to_scalar(message: &[u8]) -> BlsScalar {
    let digest = Sha256::digest(message);
    let mut wide = [0u8; 64];
    wide[..32].copy_from_slice(&digest);
    BlsScalar::from_bytes_wide(&wide)
}

pub fn sign_schnorr_babyjubjub(private_key_hex: &str, message: &[u8]) -> Result<String, String> {
    let key_bytes = hex::decode(private_key_hex)
        .map_err(|e| format!("Failed to decode hex private key: {e}"))?;

    if key_bytes.len() < 32 {
        return Err("Private key must be at least 32 bytes".to_string());
    }

    let mut sk_seed = [0u8; 32];
    sk_seed.copy_from_slice(&key_bytes[..32]);

    let mut rng = StdRng::from_seed(sk_seed);
    let secret = SecretKey::random(&mut rng);
    let scalar = message_to_scalar(message);
    let sig: Signature = secret.sign(&mut rng, scalar);
    Ok(hex::encode(sig.to_bytes()))
}

pub fn sign_hmac_sha256(secret: &str, message: &str) -> String {
    use hmac::{Hmac, Mac};
    use sha2::Sha256;

    type HmacSha256 = Hmac<Sha256>;

    let mut mac =
        HmacSha256::new_from_slice(secret.as_bytes()).expect("HMAC can take key of any size");
    mac.update(message.as_bytes());
    let result = mac.finalize();
    hex::encode(result.into_bytes())
}
