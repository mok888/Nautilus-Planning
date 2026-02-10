from typing import Optional

from nautilus_trader.common.config import PositiveFloat
from nautilus_trader.common.config import PositiveInt
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.model.identifiers import Venue


class edgexDataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for ``edgexDataClient`` instances.

    Parameters
    ----------
    api_key : str, optional
        The API public key.
        If ``None`` then will source the `EDGEX_API_KEY` environment variable.
    api_secret : str, optional
        The API secret key.
        If ``None`` then will source the `EDGEX_API_SECRET` environment variable.
    base_url_http : str, optional
        The base URL for HTTP API.
        If ``None`` then will use the default URL based on environment.
    base_url_ws : str, optional
        The base URL for WebSocket API.
        If ``None`` then will use the default URL based on environment.
    http_proxy_url : str, optional
        Optional HTTP proxy URL.
    ws_proxy_url : str, optional
        Optional WebSocket proxy URL.
    is_testnet : bool, default False
        If the client is connecting to the testnet environment.
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


class edgexExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for ``edgexExecutionClient`` instances.
    
    Parameters
    ----------
    api_key : str
        The API public key.
    api_secret : str
        The API secret key.
    base_url_http : str, optional
        The base URL for HTTP API.
    # ... (add other fields matching DataClientConfig as needed)
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
