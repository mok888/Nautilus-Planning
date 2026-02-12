pub mod ws_replay;

/// Test utilities for the Edgex adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://testnet.edgex.exchange".to_string()
}

pub fn test_ws_url() -> String {
    "wss://quote.edgex.exchange".to_string()
}
