#[cfg(test)]
mod tests {
    use crate::http::parse::{
        parse_info_response, parse_orderbook_response, parse_trades_response,
    };
    use crate::http::signing::{sign_ed25519, sign_hmac_sha256};

    // ── Signing tests ──────────────────────────────────────────────────

    #[test]
    fn test_sign_ed25519_produces_64_byte_signature() {
        // A deterministic 32-byte secret key encoded as base58
        let secret_bytes = [1u8; 32];
        let secret_b58 = bs58::encode(&secret_bytes).into_string();

        let message = b"test message";
        let sig = sign_ed25519(&secret_b58, message).expect("signing should succeed");

        assert_eq!(sig.len(), 64, "Ed25519 signature must be 64 bytes");
    }

    #[test]
    fn test_sign_ed25519_deterministic() {
        let secret_bytes = [42u8; 32];
        let secret_b58 = bs58::encode(&secret_bytes).into_string();

        let message = b"deterministic test";
        let sig1 = sign_ed25519(&secret_b58, message).unwrap();
        let sig2 = sign_ed25519(&secret_b58, message).unwrap();

        assert_eq!(sig1, sig2, "Same key + same message must produce same signature");
    }

    #[test]
    fn test_sign_ed25519_different_messages_produce_different_sigs() {
        let secret_bytes = [7u8; 32];
        let secret_b58 = bs58::encode(&secret_bytes).into_string();

        let sig1 = sign_ed25519(&secret_b58, b"message A").unwrap();
        let sig2 = sign_ed25519(&secret_b58, b"message B").unwrap();

        assert_ne!(sig1, sig2, "Different messages must produce different signatures");
    }

    #[test]
    fn test_sign_ed25519_invalid_base58_errors() {
        let result = sign_ed25519("not-valid-base58!!!", b"test");
        assert!(result.is_err(), "Invalid base58 should produce an error");
    }

    #[test]
    fn test_sign_ed25519_short_key_errors() {
        // Only 16 bytes — too short
        let short_key = bs58::encode(&[0u8; 16]).into_string();
        let result = sign_ed25519(&short_key, b"test");
        assert!(result.is_err(), "Key shorter than 32 bytes should error");
    }

    #[test]
    fn test_sign_hmac_sha256_deterministic() {
        let sig1 = sign_hmac_sha256("secret", "message");
        let sig2 = sign_hmac_sha256("secret", "message");
        assert_eq!(sig1, sig2);
    }

    #[test]
    fn test_sign_hmac_sha256_different_secrets() {
        let sig1 = sign_hmac_sha256("secret_a", "message");
        let sig2 = sign_hmac_sha256("secret_b", "message");
        assert_ne!(sig1, sig2);
    }

    #[test]
    fn test_sign_hmac_sha256_is_hex_encoded() {
        let sig = sign_hmac_sha256("key", "data");
        assert!(sig.chars().all(|c| c.is_ascii_hexdigit()), "HMAC signature must be hex-encoded");
    }

    // ── Parse tests ────────────────────────────────────────────────────

    #[test]
    fn test_parse_info_response() {
        let json = r#"{
            "markets": [{
                "marketId": 1,
                "symbol": "BTC-PERP",
                "priceDecimals": 2,
                "sizeDecimals": 6,
                "baseTokenId": 1,
                "quoteTokenId": 0,
                "imf": 0.05,
                "mmf": 0.025,
                "cmf": 0.01
            }],
            "tokens": [{
                "tokenId": 0,
                "symbol": "USDC",
                "decimals": 6,
                "mintAddr": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "weightBps": 10000
            }]
        }"#;

        let info = parse_info_response(json).expect("should parse info response");
        assert_eq!(info.markets.len(), 1);
        assert_eq!(info.tokens.len(), 1);
        assert_eq!(info.markets[0].symbol, "BTC-PERP");
        assert_eq!(info.markets[0].price_decimals, 2);
        assert_eq!(info.tokens[0].symbol, "USDC");
    }

    #[test]
    fn test_parse_orderbook_response() {
        let json = r#"{
            "asks": [{"price": "50000.00", "size": "1.5"}],
            "bids": [{"price": "49900.00", "size": "2.0"}],
            "timestamp": 1700000000000,
            "seq_num": 42
        }"#;

        let ob = parse_orderbook_response(json).expect("should parse orderbook");
        assert_eq!(ob.asks.len(), 1);
        assert_eq!(ob.bids.len(), 1);
        assert_eq!(ob.asks[0].price, "50000.00");
        assert_eq!(ob.bids[0].size, "2.0");
        assert_eq!(ob.timestamp, 1700000000000);
    }

    #[test]
    fn test_parse_trades_response() {
        let json = r#"{
            "trades": [
                {"price": "50100.25", "size": "0.5", "side": "buy", "timestamp": 1700000001000},
                {"price": "50099.75", "size": "1.0", "side": "sell", "timestamp": 1700000002000}
            ]
        }"#;

        let trades = parse_trades_response(json).expect("should parse trades");
        assert_eq!(trades.trades.len(), 2);
        assert_eq!(trades.trades[0].side, "buy");
        assert_eq!(trades.trades[1].side, "sell");
    }

    #[test]
    fn test_parse_info_response_invalid_json() {
        let result = parse_info_response("not json at all");
        assert!(result.is_err());
    }

    #[test]
    fn test_parse_orderbook_empty_levels() {
        let json = r#"{"asks": [], "bids": [], "timestamp": 0, "seq_num": 0}"#;
        let ob = parse_orderbook_response(json).expect("should parse empty orderbook");
        assert!(ob.asks.is_empty());
        assert!(ob.bids.is_empty());
    }
}
