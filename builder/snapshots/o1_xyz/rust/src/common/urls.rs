/// Get the REST base URL for 01.xyz.
///
/// - Mainnet: `https://zo-mainnet.n1.xyz`
/// - Devnet (sandbox/testnet): `https://zo-devnet.n1.xyz`
pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "https://zo-devnet.n1.xyz".to_string()
    } else {
        "https://zo-mainnet.n1.xyz".to_string()
    }
}

/// Get the WebSocket URL for 01.xyz.
pub fn get_ws_url(_sandbox: bool) -> String {
    "wss://api.o1.exchange/ws".to_string()
}
