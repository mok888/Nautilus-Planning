pub mod ws_replay;

/// Test utilities for the O1Xyz adapter.
/// Enabled with `--features test_utils` or `#[cfg(test)]`.
pub fn test_base_url() -> String {
    "https://zo-devnet.n1.xyz".to_string()
}

pub fn test_ws_url() -> String {
    "wss://api.o1.exchange/ws".to_string()
}
