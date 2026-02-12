/// Get the REST base URL for Edgex.
///
/// - Mainnet: `https://pro.edgex.exchange`
/// - Devnet (sandbox/testnet): `https://testnet.edgex.exchange`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://testnet.edgex.exchange".to_string()
    } else {
        "https://pro.edgex.exchange".to_string()
    }
}

/// Get the WebSocket URL for Edgex.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://quote.edgex.exchange".to_string()
}
