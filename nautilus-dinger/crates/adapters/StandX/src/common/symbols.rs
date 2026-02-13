pub fn normalize_symbol_to_nautilus(input: &str) -> String {
    let mut upper = input.trim().to_ascii_uppercase().replace('/', "-").replace('_', "-");

    while upper.ends_with('-') {
        upper.pop();
    }

    if upper.ends_with("-PERP") {
        return upper;
    }

    if upper.ends_with("PERP") {
        upper = upper.trim_end_matches("PERP").trim_end_matches('-').to_string();
    }

    if upper.contains('-') {
        let parts: Vec<&str> = upper.split('-').filter(|part| !part.is_empty()).collect();
        if parts.len() >= 3 && parts[parts.len() - 1] == "PERP" {
            return parts.join("-");
        }
        if parts.len() >= 2 {
            return format!("{}-{}-PERP", parts[0], parts[1]);
        }
    }

    for quote in ["USDC", "USDT", "USD"] {
        if upper.ends_with(quote) && upper.len() > quote.len() {
            let base = &upper[..upper.len() - quote.len()];
            return format!("{}-{}-PERP", base, quote);
        }
    }

    format!("{}-USD-PERP", upper)
}

pub fn normalize_symbol_to_venue(input: &str) -> String {
    let normalized = normalize_symbol_to_nautilus(input);
    if let Some(stripped) = normalized.strip_suffix("-PERP") {
        stripped.to_string()
    } else {
        normalized
    }
}
