#[cfg(test)]
mod tests {
    use crate::http::parse::{
        parse_info_response, parse_orderbook_response, parse_trades_response,
    };
    use crate::http::signing::{auth_message_hash, sign_auth_message, OrderParams};

    // ── Signing tests ──────────────────────────────────────────────────

    #[test]
    fn test_sign_auth_produces_valid_signature() {
        let secret_hex = hex::encode([1u8; 32]);
        let account_hex = hex::encode([2u8; 32]);
        let sig = sign_auth_message(
            &secret_hex,
            &account_hex,
            "PRIVATE_SN_POTC_SEPOLIA",
            1_700_000_000,
            1_700_086_400,
        )
        .expect("signing should succeed");
        assert!(
            sig.starts_with("[") && sig.ends_with("]"),
            "Paradex sig must be decimal string array"
        );
    }

    #[test]
    fn test_sign_auth_deterministic() {
        let secret_hex = hex::encode([1u8; 32]);
        let account_hex = hex::encode([2u8; 32]);
        let sig1 = sign_auth_message(
            &secret_hex,
            &account_hex,
            "PRIVATE_SN_POTC_SEPOLIA",
            1_700_000_000,
            1_700_086_400,
        )
        .unwrap();
        let sig2 = sign_auth_message(
            &secret_hex,
            &account_hex,
            "PRIVATE_SN_POTC_SEPOLIA",
            1_700_000_000,
            1_700_086_400,
        )
        .unwrap();
        assert_eq!(sig1, sig2, "Same key + same message must produce same signature");
    }

    #[test]
    fn test_sign_auth_different_timestamps_produce_different_sigs() {
        let secret_hex = hex::encode([1u8; 32]);
        let account_hex = hex::encode([2u8; 32]);
        let sig1 = sign_auth_message(
            &secret_hex,
            &account_hex,
            "PRIVATE_SN_POTC_SEPOLIA",
            1_700_000_000,
            1_700_086_400,
        )
        .unwrap();
        let sig2 = sign_auth_message(
            &secret_hex,
            &account_hex,
            "PRIVATE_SN_POTC_SEPOLIA",
            1_700_000_001,
            1_700_086_401,
        )
        .unwrap();
        assert_ne!(sig1, sig2, "Different messages must produce different signatures");
    }

    #[test]
    fn test_sign_auth_invalid_key_errors() {
        let account_hex = hex::encode([2u8; 32]);
        let result = sign_auth_message(
            "not-valid-hex-zzz",
            &account_hex,
            "PRIVATE_SN_POTC_SEPOLIA",
            1_700_000_000,
            1_700_086_400,
        );
        assert!(result.is_err(), "Invalid key should produce an error");
    }

    #[test]
    fn test_sign_auth_invalid_account_errors() {
        let secret_hex = hex::encode([1u8; 32]);
        let result = sign_auth_message(
            &secret_hex,
            "not-valid-hex-zzz",
            "PRIVATE_SN_POTC_SEPOLIA",
            1_700_000_000,
            1_700_086_400,
        );
        assert!(result.is_err(), "Invalid account hex should produce an error");
    }

    #[test]
    fn test_auth_hash_matches_paradex_py_vector() {
        let account_hex = "0x4b23c8b4ea5dc54b63fbab3852f2bb0c447226f21c668bb7ba63277e322c5e8";
        let hash =
            auth_message_hash(account_hex, "PRIVATE_SN_POTC_SEPOLIA", 1_770_786_025, 1_770_872_425)
                .expect("hash must compute");

        assert_eq!(
            hash.to_string(),
            "102723934277454906827628273749418461536092790735476798625340775014036361666"
        );
    }

    #[test]
    fn test_order_params_constructible() {
        let params = OrderParams {
            chain_id: "PRIVATE_SN_POTC_SEPOLIA".to_string(),
            timestamp: 1_700_000_000_000,
            market: "BTC-USD-PERP".to_string(),
            side: "1".to_string(),
            order_type: "LIMIT".to_string(),
            size: "1000000".to_string(),
            price: "5000000000000".to_string(),
        };

        assert_eq!(params.market, "BTC-USD-PERP");
    }

    // ── Parse tests ────────────────────────────────────────────────────

    #[test]
    fn test_parse_info_response() {
        let json = r#"{
            "results": [{
                "symbol": "BTC-USD-PERP",
                "base_currency": "BTC",
                "quote_currency": "USD",
                "settlement_currency": "USDC",
                "order_size_increment": "0.00001",
                "price_tick_size": "0.1",
                "min_notional": "100",
                "open_at": 1700000000000,
                "expiry_at": 0,
                "asset_kind": "PERP",
                "market_kind": "cross"
            }]
        }"#;

        let info = parse_info_response(json).expect("should parse info response");
        assert_eq!(info.results.len(), 1);
        assert_eq!(info.results[0].symbol, "BTC-USD-PERP");
        assert_eq!(info.results[0].price_tick_size, "0.1");
        assert_eq!(info.results[0].settlement_currency, "USDC");
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
        assert_eq!(ob.timestamp, Some(1700000000000));
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
