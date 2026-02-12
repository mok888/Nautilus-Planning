/// Get the REST base URL for ApexOmni.
///
/// - Mainnet: `https://omni.apex.exchange/api`
/// - Devnet (sandbox/testnet): `https://omni.testnet.apex.exchange/api`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://omni.testnet.apex.exchange/api".to_string()
    } else {
        "https://omni.apex.exchange/api".to_string()
    }
}

/// Get the WebSocket URL for ApexOmni.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://omni.apex.exchange/ws/v3".to_string()
}
