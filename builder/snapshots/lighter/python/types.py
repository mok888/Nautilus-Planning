# ------------------------------------------------------------------------------
#  Copyright (c) 2024 Nautilus Technologies, Inc.
#  ------------------------------------------------------------------------------

import msgspec


class LighterOrderBookMsg(msgspec.Struct, tag="orderbook"):
    asks: list[list[float]]
    bids: list[list[float]]
    symbol: str
    timestamp: int


class LighterTradeMsg(msgspec.Struct, tag="trade"):
    id: str
    price: float
    quantity: float
    side: str
    timestamp: int
    symbol: str


class LighterOrderResponse(msgspec.Struct):
    orderId: str
    status: str
    symbol: str


class LighterCancelOrderResponse(msgspec.Struct):
    orderId: str
    status: str
