from typing import Optional

from nautilus_trader.common.config import PositiveFloat
from nautilus_trader.common.config import PositiveInt
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.model.identifiers import Venue


class O1XyzDataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for ``O1XyzDataClient`` instances.

    Parameters
    ----------
    api_key : str, optional
        The API public key for Bearer token auth.
        If ``None`` then will source the `O1_XYZ_API_KEY` environment variable.
    api_secret : str, optional
        The API secret key (Solana Ed25519 private key).
        If ``None`` then will source the `O1_XYZ_API_SECRET` environment variable.
    base_url_http : str, optional
        The base URL for HTTP API.
        If ``None`` then will use ``https://zo-mainnet.n1.xyz``.
    base_url_ws : str, optional
        The base URL for WebSocket API.
        If ``None`` then will use ``wss://api.o1.exchange/ws``.
    http_proxy_url : str, optional
        Optional HTTP proxy URL.
    ws_proxy_url : str, optional
        Optional WebSocket proxy URL.
    is_testnet : bool, default False
        If the client is connecting to the testnet (devnet) environment.
    http_timeout_secs : PositiveInt, default 60
        The timeout for HTTP requests in seconds.
    max_retries : PositiveInt, optional
        The maximum number of retries for HTTP requests.
    retry_delay_initial_ms : PositiveInt, default 1_000
        The initial delay (milliseconds) between retries.
    retry_delay_max_ms : PositiveInt, default 5_000
        The maximum delay (milliseconds) between retries.
    update_instruments_interval_mins: PositiveInt or None, default 60
        The interval (minutes) between reloading instruments from the venue.
    max_requests_per_second : PositiveInt, default 10
        The maximum number of requests per second (rate limit).

    """

    api_key: str | None = None
    api_secret: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    http_proxy_url: str | None = None
    ws_proxy_url: str | None = None
    is_testnet: bool = False
    http_timeout_secs: PositiveInt | None = 60
    max_retries: PositiveInt | None = 3
    retry_delay_initial_ms: PositiveInt | None = 1_000
    retry_delay_max_ms: PositiveInt | None = 5_000
    update_instruments_interval_mins: PositiveInt | None = 60
    max_requests_per_second: PositiveInt = 10


class O1XyzExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for ``O1XyzExecutionClient`` instances.

    Parameters
    ----------
    api_key : str, optional
        The API public key for Bearer token auth.
    api_secret : str, optional
        The API secret key (Solana Ed25519 private key).
    base_url_http : str, optional
        The base URL for HTTP API.
    base_url_ws : str, optional
        The base URL for WebSocket API.
    is_testnet : bool, default False
        If the client is connecting to the testnet (devnet) environment.

    """

    api_key: str | None = None
    api_secret: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    http_proxy_url: str | None = None
    ws_proxy_url: str | None = None
    is_testnet: bool = False
    http_timeout_secs: PositiveInt | None = 60
    max_retries: PositiveInt | None = 3
    retry_delay_initial_ms: PositiveInt | None = 1_000
    retry_delay_max_ms: PositiveInt | None = 5_000
