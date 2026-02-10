pub fn get_rest_url(sandbox: bool) -> String {
    if sandbox {
        "{{REST_URL_TESTNET}}".to_string()
    } else {
        "https://pro.edgex.exchange".to_string()
    }
}
