from pydantic import BaseModel
from typing import List, Optional


class Endpoint(BaseModel):
    path: str
    method: str
    purpose: str


class ExchangeSpec(BaseModel):
    name: str
    rest_base: str
    ws_base: str
    auth: str
    endpoints: List[Endpoint]
