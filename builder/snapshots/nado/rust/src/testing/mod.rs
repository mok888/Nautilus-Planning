pub mod ws_replay;

/// Test utilities for the Nado adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://gateway.testnet.nado.xyz".to_string()
}

pub fn test_ws_url() -> String {
    "wss://gateway.prod.nado.xyz/ws".to_string()
}
