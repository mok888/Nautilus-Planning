pub mod ws_replay;

/// Test utilities for the Paradex adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://api.testnet.paradex.trade/v1".to_string()
}

pub fn test_ws_url() -> String {
    "wss://ws.api.prod.paradex.trade/v1".to_string()
}
