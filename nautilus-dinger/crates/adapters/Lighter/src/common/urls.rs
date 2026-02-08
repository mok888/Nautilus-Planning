pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "{{REST_URL_TESTNET}}".to_string()
    } else {
        "https://api.lighter.xyz".to_string()
    }
}
