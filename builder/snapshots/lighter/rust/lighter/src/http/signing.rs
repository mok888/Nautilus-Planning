// Copyright (C) 2024 Nautilus Technologies, Inc.
// SPDX-License-Identifier: MIT

use crate::error::Result;
use chrono::Utc;
use hmac::{Hmac, Mac, NewMac};
use sha2::Sha256;
use std::fmt::Write;

type HmacSha256 = Hmac<Sha256>;

/// Generates the required headers for authenticated requests to Lighter.
///
/// According to the schema:
/// - Headers: x-lighter-chain-id, x-api-key, x-timestamp, x-signature
/// - Payload: timestamp + method + requestPath + body
/// - Encoding: hex
pub fn generate_headers(
    api_key: &str,
    api_secret: &str,
    chain_id: &str,
    method: &str,
    path: &str,
    body: &str,
) -> Result<Vec<(String, String)>> {
    let timestamp = Utc::now().timestamp_millis().to_string();

    // Construct signature payload: timestamp + method + requestPath + body
    let mut payload = String::new();
    write!(&mut payload, "{}{}{}{}", timestamp, method, path, body)
        .map_err(|e| crate::error::LighterAdapterError::Signing(format!("Failed to format payload: {}", e)))?;

    // Sign using HMAC-SHA256
    let mut mac = HmacSha256::new_from_slice(api_secret.as_bytes())
        .map_err(|e| crate::error::LighterAdapterError::Signing(format!("Invalid secret key: {}", e)))?;
    mac.update(payload.as_bytes());
    let signature_bytes = mac.finalize().into_bytes();
    let signature = hex::encode(signature_bytes);

    let headers = vec![
        ("x-lighter-chain-id".to_string(), chain_id.to_string()),
        ("x-api-key".to_string(), api_key.to_string()),
        ("x-timestamp".to_string(), timestamp),
        ("x-signature".to_string(), signature),
    ];

    Ok(headers)
}
