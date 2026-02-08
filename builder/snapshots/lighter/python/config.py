# ------------------------------------------------------------------------------
#  Copyright (c) 2024 Nautilus Technologies, Inc.
#  ------------------------------------------------------------------------------

from nautilus_trader.config import InstrumentProviderConfig, ExecutionClientConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.model.data import DataType
from os import getenv


class LighterConfig:
    """
    Base configuration class for the Lighter adapter.
    """
    pass


class LighterInstrumentProviderConfig(InstrumentProviderConfig, kw_only=True):
    """
    Configuration for ``LighterInstrumentProvider``.

    Parameters
    ----------
    api_key : str, optional
        The API key for Lighter.
    api_secret : str, optional
        The API secret for Lighter.
    chain_id : str, optional
        The chain ID for the Lighter DEX (e.g., '137' for Polygon).
        If None, defaults to Polygon Mainnet.
    """

    api_key: str | None = None
    api_secret: str | None = None
    chain_id: str = "137"


class LighterExecClientConfig(ExecutionClientConfig, kw_only=True):
    """
    Configuration for ``LighterExecutionClient``.

    Parameters
    ----------
    api_key : str, optional
        The API key for Lighter. If ``None`` then will try to read from the environment variable ``Lighter_API_KEY``.
    api_secret : str, optional
        The API secret for Lighter. If ``None`` then will try to read from the environment variable ``Lighter_API_SECRET``.
    chain_id : str, optional
        The chain ID for the Lighter DEX (e.g., '137' for Polygon).
    """

    api_key: str | None = None
    api_secret: str | None = None
    chain_id: str = "137"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = getenv("Lighter_API_KEY")
        if self.api_secret is None:
            self.api_secret = getenv("Lighter_API_SECRET")

        PyCondition.not_none(self.api_key, "api_key")
        PyCondition.not_none(self.api_secret, "api_secret")
