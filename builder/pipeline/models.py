from pydantic import BaseModel
from typing import List, Literal, Union

UNKNOWN = Literal["UNKNOWN"]

class ExchangeIdentity(BaseModel):
    exchange_name: str
    venue_id: str
    exchange_type: Literal["CEX", "DEX"]

class MarketCoverage(BaseModel):
    spot_supported: bool
    perps_supported: bool
    futures_supported: Union[bool, UNKNOWN]
    options_supported: Union[bool, UNKNOWN]

class RestAPI(BaseModel):
    rest_base_url: str
    api_version: str
    rate_limits: List[Union[dict, UNKNOWN]]

class Authentication(BaseModel):
    auth_type: Literal["HMAC", "JWT", "WALLET", "API_KEY", "SIGNATURE"]
    headers: List[str]
    timestamp_format: str
    signature_payload: str
    hash_algo: str
    encoding: str
    passphrase_required: Union[bool, UNKNOWN]

class RestEndpoint(BaseModel):
    name: str
    path: str
    method: Literal["GET", "POST", "DELETE"]
    auth_required: bool
    request_fields: List[str]
    response_fields: List[str]

class WebSocketPublic(BaseModel):
    ws_public_url: str
    channels: List[Union[str, dict]]
    heartbeat_interval_sec: Union[int, UNKNOWN]

class WebSocketPrivate(BaseModel):
    ws_private_url: str
    auth_required: Union[bool, UNKNOWN]
    order_updates: Union[bool, UNKNOWN]
    fills: Union[bool, UNKNOWN]
    balance_updates: Union[bool, UNKNOWN]

class OrderModel(BaseModel):
    order_types: List[str]
    order_states: List[str]
    partial_fill_behavior: str
    cancel_behavior: str

class InstrumentMetadata(BaseModel):
    instrument_id_format: str
    price_precision: Union[str, int, UNKNOWN]
    quantity_precision: Union[str, int, UNKNOWN]
    contract_size: Union[str, int, float, UNKNOWN]

class ExchangeResearch(BaseModel):
    exchange_identity: ExchangeIdentity
    market_coverage: MarketCoverage
    rest_api: RestAPI
    authentication: Authentication
    rest_endpoints: List[RestEndpoint]
    websocket_public: WebSocketPublic
    websocket_private: WebSocketPrivate
    order_model: OrderModel
    instrument_metadata: InstrumentMetadata
    special_notes: List[str]
