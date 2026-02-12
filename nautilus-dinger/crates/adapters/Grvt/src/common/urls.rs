/// Get the REST base URL for Grvt.
///
/// - Mainnet: `https://edge.grvt.io`
/// - Devnet (sandbox/testnet): `https://edge.testnet.grvt.io`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://edge.testnet.grvt.io".to_string()
    } else {
        "https://edge.grvt.io".to_string()
    }
}

/// Get the WebSocket URL for Grvt.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://trades.grvt.io/ws/full".to_string()
}
