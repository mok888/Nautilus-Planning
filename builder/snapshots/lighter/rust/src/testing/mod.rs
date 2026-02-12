pub mod ws_replay;

/// Test utilities for the Lighter adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://testnet.zklighter.elliot.ai".to_string()
}

pub fn test_ws_url() -> String {
    "wss://mainnet.zklighter.elliot.ai/stream".to_string()
}
