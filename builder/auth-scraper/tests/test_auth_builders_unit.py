from src.auth_builders import edgex_hmac_signature


def test_edgex_signature_deterministic() -> None:
    hdr1 = edgex_hmac_signature(
        private_key=b"secret",
        timestamp_ms=1700000000000,
        method="GET",
        path="/api/v1/account",
        payload_bytes=b"",
    )
    hdr2 = edgex_hmac_signature(
        private_key=b"secret",
        timestamp_ms=1700000000000,
        method="GET",
        path="/api/v1/account",
        payload_bytes=b"",
    )
    assert hdr1.signature_hex == hdr2.signature_hex
    assert len(hdr1.signature_hex) == 64


def test_backpack_signature_with_base58_string() -> None:
    # Random 32 bytes encoded as base58
    # 32 bytes of 0x01 is:
    # 11111111111111111111111111111111
    # Base58 of 32 bytes of 0x00 is: 11111111111111111111111111111111
    
    # Let's use a known key-pair for deterministic testing if possible, or just check execution.
    # We'll just check it runs and produces base64.
    
    # 32 bytes key
    import base58
    from src.auth_builders import backpack_sign_ed25519
    
    priv_bytes = b"\x01" * 32
    priv_b58 = base58.b58encode(priv_bytes).decode("ascii")
    
    hdr = backpack_sign_ed25519(
        api_key="key",
        private_key_base58_or_bytes=priv_b58,
        message=b"hello",
        timestamp_ms=123,
    )
    assert len(hdr.signature_b64) > 10


def test_backpack_signature_with_bytes() -> None:
    from src.auth_builders import backpack_sign_ed25519
    
    priv_bytes = b"\x02" * 32
    
    hdr = backpack_sign_ed25519(
        api_key="key",
        private_key_base58_or_bytes=priv_bytes,
        message=b"hello",
        timestamp_ms=123,
    )
    assert len(hdr.signature_b64) > 10


def test_standx_signature_smoke() -> None:
    # StandX uses the same Ed25519 logic, just checks it returns the new dataclass
    import base58
    from src.auth_builders import standx_sign_ed25519, StandxAuthHeaders

    priv_bytes = b"\x03" * 32
    priv_b58 = base58.b58encode(priv_bytes).decode("ascii")

    hdr = standx_sign_ed25519(
        private_key_base58_or_bytes=priv_b58,
        message=b"hello_standx",
    )
    assert isinstance(hdr, StandxAuthHeaders)
    assert len(hdr.signature_hex) == 128  # 64 bytes hex encoded


def test_grvt_signature_smoke() -> None:
    from src.auth_builders import grvt_sign, GrvtAuthHeaders
    
    # 32 bytes priv key 0x...
    priv_hex = "0x" + "04" * 32
    hdr = grvt_sign(private_key_hex=priv_hex, message=b"hello_grvt")
    
    assert isinstance(hdr, GrvtAuthHeaders)
    assert len(hdr.signature_hex) == 128


def test_lighter_signature_smoke() -> None:
    from src.auth_builders import lighter_sign, LighterAuthHeaders
    
    # 40 bytes hex (80 chars) key from example
    priv_hex = "2b2eb5fd7b1bd3b62e34033b0583b15614c004c7d979075cf299be548dcf66e1fec137d3c3bc8b1d"
    
    hdr = lighter_sign(
        private_key_hex=priv_hex,
        message=b"hello_lighter",
        api_key_index=1,
        timestamp_ms=1600000000000,
        account_index=12345
    )
    
    assert isinstance(hdr, LighterAuthHeaders)
    # If SDK is installed (it is in our env), auth_token should be present
    try:
        import lighter
        assert hdr.auth_token is not None
        assert len(hdr.auth_token) > 10
    except ImportError:
        assert len(hdr.signature_hex) > 0
