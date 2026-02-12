/// Get the REST base URL for Paradex.
///
/// - Mainnet: `https://api.prod.paradex.trade/v1`
/// - Devnet (sandbox/testnet): `https://api.testnet.paradex.trade/v1`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://api.testnet.paradex.trade/v1".to_string()
    } else {
        "https://api.prod.paradex.trade/v1".to_string()
    }
}

/// Get the WebSocket URL for Paradex.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://ws.api.prod.paradex.trade/v1".to_string()
}
