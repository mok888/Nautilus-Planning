pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "{{REST_URL_TESTNET}}".to_string()
    } else {
        "{{REST_URL_MAINNET}}".to_string()
    }
}
