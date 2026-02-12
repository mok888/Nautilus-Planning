pub mod ws_replay;

/// Test utilities for the ApexOmni adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://omni.testnet.apex.exchange/api".to_string()
}

pub fn test_ws_url() -> String {
    "wss://omni.apex.exchange/ws/v3".to_string()
}
