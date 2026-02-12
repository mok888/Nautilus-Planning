pub mod ws_replay;

/// Test utilities for the Grvt adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://edge.testnet.grvt.io".to_string()
}

pub fn test_ws_url() -> String {
    "wss://trades.grvt.io/ws/full".to_string()
}
