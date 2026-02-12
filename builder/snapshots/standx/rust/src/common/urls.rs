/// Get the REST base URL for StandX.
///
/// - Mainnet: `https://perps.standx.com`
/// - Devnet (sandbox/testnet): `https://testnet.perps.standx.com`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://testnet.perps.standx.com".to_string()
    } else {
        "https://perps.standx.com".to_string()
    }
}

/// Get the WebSocket URL for StandX.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://perps.standx.com/ws-stream/v1".to_string()
}
