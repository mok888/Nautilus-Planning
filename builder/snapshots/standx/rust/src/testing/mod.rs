pub mod ws_replay;

/// Test utilities for the StandX adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://testnet.perps.standx.com".to_string()
}

pub fn test_ws_url() -> String {
    "wss://perps.standx.com/ws-stream/v1".to_string()
}
