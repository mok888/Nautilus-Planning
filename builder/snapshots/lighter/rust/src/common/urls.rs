/// Get the REST base URL for Lighter.
///
/// - Mainnet: `https://mainnet.zklighter.elliot.ai`
/// - Devnet (sandbox/testnet): `https://testnet.zklighter.elliot.ai`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://testnet.zklighter.elliot.ai".to_string()
    } else {
        "https://mainnet.zklighter.elliot.ai".to_string()
    }
}

/// Get the WebSocket URL for Lighter.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://mainnet.zklighter.elliot.ai/stream".to_string()
}
