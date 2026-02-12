/// Get the REST base URL for Nado.
///
/// - Mainnet: `https://gateway.prod.nado.xyz`
/// - Devnet (sandbox/testnet): `https://gateway.testnet.nado.xyz`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://gateway.testnet.nado.xyz".to_string()
    } else {
        "https://gateway.prod.nado.xyz".to_string()
    }
}

/// Get the WebSocket URL for Nado.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://gateway.prod.nado.xyz/ws".to_string()
}
