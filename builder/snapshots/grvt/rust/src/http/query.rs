/// Build a query string from key-value pairs.
pub fn build_query_string(params: &[(&str, &str)]) -> String {
    if params.is_empty() {
        return String::new();
    }
    let pairs: Vec<String> = params
        .iter()
        .map(|(k, v)| format!("{}={}", k, v))
        .collect();
    format!("?{}", pairs.join("&"))
}

/// Build the full URL for a REST endpoint with optional query parameters.
pub fn build_url(base_url: &str, path: &str, params: &[(&str, &str)]) -> String {
    let query = build_query_string(params);
    format!("{}{}{}", base_url, path, query)
}
