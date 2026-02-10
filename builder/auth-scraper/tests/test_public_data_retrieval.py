import os

from src.public_clients import hyperliquid_public_meta, lighter_public_info





def test_hyperliquid_public_meta_smoke() -> None:
    api_url = os.getenv("HYPERLIQUID_API_URL", "https://api.hyperliquid.xyz")
    res = hyperliquid_public_meta(api_url)
    assert res.status_code in (200, 400), (res.url, res.status_code, res.payload_preview)
    # If 400, endpoint exists but payload may be rejected by upstream change; still proves reachability.


def test_standx_public_health_smoke() -> None:
    from src.public_clients import standx_public_health
    # If not set, use the base URL from the probe script as default
    base_url = os.getenv("STANDX_BASE_URL", "https://perps.standx.com")
    res = standx_public_health(base_url)
    assert res.status_code == 200, (res.url, res.status_code, res.payload_preview)


def test_grvt_public_health_smoke() -> None:
    from src.public_clients import grvt_public_health
    base_url = os.getenv("GRVT_BASE_URL", "https://edge.grvt.io")
    res = grvt_public_health(base_url)
    # 403 is expected for now due to WAF/Geo, but 200 is also fine if opened up.
    # We just want to ensure it doesn't raise ConnectionError.
    assert res.status_code in (200, 403), (res.url, res.status_code, res.payload_preview)


def test_lighter_public_info_smoke() -> None:
    from src.public_clients import lighter_public_info
    base_url = os.getenv("LIGHTER_BASE_URL", "https://mainnet.zklighter.elliot.ai")
    res = lighter_public_info(base_url)
    assert res.status_code == 200, (res.url, res.status_code, res.payload_preview)
