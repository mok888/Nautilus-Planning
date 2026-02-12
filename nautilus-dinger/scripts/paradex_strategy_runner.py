import argparse
import json
import os
import sys
import threading
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol, cast


class _ParadexOrderbookClient(Protocol):
    def get_orderbook(self, symbol: str) -> str | dict:
        ...


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _ensure_paradex_extension(repo_root: Path) -> None:
    debug_dir = repo_root / "target" / "debug"
    extension_path = debug_dir / "paradex.so"
    lib_path = debug_dir / "libparadex.so"

    if not extension_path.exists() and lib_path.exists():
        try:
            os.symlink(lib_path.name, extension_path)
        except FileExistsError:
            pass

    if str(debug_dir) not in sys.path:
        sys.path.insert(0, str(debug_dir))


@dataclass
class RuntimePlan:
    entry_price: Decimal
    tp_price: Decimal
    sl_trigger_price: Decimal


def _build_runtime_plan(
    side: str,
    ref_bid: Decimal,
    ref_ask: Decimal,
    entry_bps: Decimal,
    tp_pct: Decimal,
    sl_pct: Decimal,
) -> RuntimePlan:
    side_upper = side.upper()
    bps = entry_bps / Decimal("10000")

    if side_upper == "BUY":
        entry = ref_ask * (Decimal("1") + bps)
        tp = entry * (Decimal("1") + tp_pct / Decimal("100"))
        sl = entry * (Decimal("1") - sl_pct / Decimal("100"))
    else:
        entry = ref_bid * (Decimal("1") - bps)
        tp = entry * (Decimal("1") - tp_pct / Decimal("100"))
        sl = entry * (Decimal("1") + sl_pct / Decimal("100"))

    return RuntimePlan(entry_price=entry, tp_price=tp, sl_trigger_price=sl)


def _get_reference_prices(http_client: _ParadexOrderbookClient, symbol: str) -> tuple[Decimal, Decimal]:
    payload = http_client.get_orderbook(symbol)
    data = json.loads(payload) if isinstance(payload, str) else payload
    bids = data.get("bids", [])
    asks = data.get("asks", [])
    if not bids or not asks:
        raise RuntimeError(f"Orderbook for {symbol} has no bids/asks")

    best_bid = Decimal(str(bids[0]["price"] if isinstance(bids[0], dict) else bids[0][0]))
    best_ask = Decimal(str(asks[0]["price"] if isinstance(asks[0], dict) else asks[0][0]))
    return best_bid, best_ask


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USD-PERP")
    parser.add_argument("--side", choices=["BUY", "SELL"], default="BUY")
    parser.add_argument("--quantity", type=Decimal, default=Decimal("0.01"))
    parser.add_argument("--entry-bps", type=Decimal, default=Decimal("5"))
    parser.add_argument("--tp-pct", type=Decimal, default=Decimal("1.0"))
    parser.add_argument("--sl-pct", type=Decimal, default=Decimal("1.0"))
    parser.add_argument("--entry-order-type", choices=["LIMIT", "MARKET"], default="LIMIT")
    parser.add_argument("--modify-entry-bps", type=Decimal, default=None)
    parser.add_argument("--runtime-secs", type=int, default=45)
    parser.add_argument("--reconciliation-lookback-mins", type=int, default=120)
    parser.add_argument("--reconciliation-page-size", type=int, default=100)
    parser.add_argument("--cancel-entry-on-accept", action="store_true")
    parser.add_argument("--testnet", action="store_true", default=True)
    parser.add_argument("--trader-id", default="TRADER-001")
    parser.add_argument(
        "--env-file",
        default="crates/adapters/Paradex/env_paradex",
    )
    return parser.parse_args()


def _build_strategy_classes():
    from nautilus_trader.config import StrategyConfig
    from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
    from nautilus_trader.model.identifiers import InstrumentId
    from nautilus_trader.trading.strategy import Strategy

    class ParadexSignalStrategyConfig(StrategyConfig, frozen=True):
        instrument_id: InstrumentId
        side: str
        quantity: Decimal
        entry_price: Decimal
        tp_price: Decimal
        sl_trigger_price: Decimal
        entry_order_type: str = "LIMIT"
        modify_entry_bps: Decimal | None = None
        cancel_entry_on_accept: bool = False

    class ParadexSignalStrategy(Strategy):
        def __init__(self, config: ParadexSignalStrategyConfig) -> None:
            super().__init__(config)
            self._cancel_sent = False
            self._entry_client_order_id = None
            self._entry_canceled = False
            self._linked_child_ids = set()
            self._cancel_requested_ids = set()
            self._cancel_attempts = {}
            self._max_cancel_attempts = 2
            self._modify_sent = False

        def _try_cancel_linked_children(self) -> None:
            for child_id in list(self._linked_child_ids):
                child_key = str(child_id)
                if child_key in self._cancel_requested_ids:
                    continue
                if self._cancel_attempts.get(child_key, 0) >= self._max_cancel_attempts:
                    continue
                child_order = self.cache.order(child_id)
                if child_order is None:
                    continue
                self._cancel_requested_ids.add(child_key)
                self._cancel_attempts[child_key] = self._cancel_attempts.get(child_key, 0) + 1
                self.cancel_order(child_order)

        def on_start(self) -> None:
            instrument = self.cache.instrument(self.config.instrument_id)
            if instrument is None:
                self.log.error(f"Instrument not found in cache: {self.config.instrument_id}")
                self.stop()
                return

            qty = instrument.make_qty(self.config.quantity)
            side = OrderSide[self.config.side.upper()]
            entry_price = instrument.make_price(self.config.entry_price)
            tp_price = instrument.make_price(self.config.tp_price)
            sl_trigger_price = instrument.make_price(self.config.sl_trigger_price)

            entry_order_type = OrderType[self.config.entry_order_type.upper()]
            entry_tif = TimeInForce.IOC if entry_order_type == OrderType.MARKET else TimeInForce.GTC
            bracket_kwargs = dict(
                instrument_id=instrument.id,
                order_side=side,
                quantity=qty,
                entry_order_type=entry_order_type,
                time_in_force=entry_tif,
                tp_order_type=OrderType.LIMIT,
                tp_price=tp_price,
                sl_order_type=OrderType.STOP_MARKET,
                sl_trigger_price=sl_trigger_price,
            )
            if entry_order_type == OrderType.LIMIT:
                bracket_kwargs["entry_price"] = entry_price

            order_list = self.order_factory.bracket(**bracket_kwargs)

            self.publish_signal(
                name="trade_intent",
                value=1.0,
                ts_event=self.clock.timestamp_ns(),
            )
            self.submit_order_list(order_list)

        def on_order_submitted(self, event) -> None:
            self.log.info(f"ORDER_SUBMITTED {event.client_order_id}")

        def on_order_accepted(self, event) -> None:
            self.log.info(
                f"ORDER_ACCEPTED {event.client_order_id} venue_order_id={event.venue_order_id}",
            )

            accepted_order = self.cache.order(event.client_order_id)
            if (
                accepted_order is not None
                and self._entry_client_order_id is not None
                and getattr(accepted_order, "parent_order_id", None) is not None
                and str(getattr(accepted_order, "parent_order_id", ""))
                == str(self._entry_client_order_id)
            ):
                self._linked_child_ids.add(event.client_order_id)

            if accepted_order is not None and self._entry_canceled:
                event_key = str(event.client_order_id)
                if event.client_order_id in self._linked_child_ids:
                    if event_key not in self._cancel_requested_ids and self._cancel_attempts.get(event_key, 0) < self._max_cancel_attempts:
                        self._cancel_requested_ids.add(event_key)
                        self._cancel_attempts[event_key] = self._cancel_attempts.get(event_key, 0) + 1
                        self.cancel_order(accepted_order)

            if not self.config.cancel_entry_on_accept or self._cancel_sent:
                if (
                    not self._modify_sent
                    and self.config.modify_entry_bps is not None
                    and accepted_order is not None
                    and getattr(accepted_order, "parent_order_id", None) is None
                    and accepted_order.order_type.name == "LIMIT"
                ):
                    bps = Decimal(str(self.config.modify_entry_bps))
                    current_px = Decimal(str(accepted_order.price))
                    shifted_px = current_px * (Decimal("1") + (bps / Decimal("10000")))
                    inst = self.cache.instrument(accepted_order.instrument_id)
                    if inst is not None:
                        self._modify_sent = True
                        self.modify_order(accepted_order, price=inst.make_price(shifted_px))
                return

            if accepted_order is None:
                return
            if getattr(accepted_order, "parent_order_id", None) is not None:
                return

            self._cancel_sent = True
            self._entry_client_order_id = event.client_order_id
            self._linked_child_ids = set(getattr(accepted_order, "linked_order_ids", []) or [])
            self._cancel_requested_ids.add(str(event.client_order_id))
            self.cancel_order(accepted_order)

        def on_order_rejected(self, event) -> None:
            self.log.error(f"ORDER_REJECTED {event.client_order_id} reason={event.reason}")

        def on_order_canceled(self, event) -> None:
            self.log.info(f"ORDER_CANCELED {event.client_order_id}")
            if self._entry_client_order_id is not None and event.client_order_id == self._entry_client_order_id:
                self._entry_canceled = True
                self._try_cancel_linked_children()

        def on_order_cancel_rejected(self, event) -> None:
            event_key = str(event.client_order_id)
            self._cancel_requested_ids.discard(event_key)
            if self._entry_canceled and event.client_order_id in self._linked_child_ids:
                child_order = self.cache.order(event.client_order_id)
                if child_order is not None and self._cancel_attempts.get(event_key, 0) < self._max_cancel_attempts:
                    self._cancel_requested_ids.add(event_key)
                    self._cancel_attempts[event_key] = self._cancel_attempts.get(event_key, 0) + 1
                    self.cancel_order(child_order)
            self.log.error(
                f"ORDER_CANCEL_REJECTED {event.client_order_id} reason={event.reason}",
            )

        def on_order_filled(self, event) -> None:
            self.log.info(
                f"ORDER_FILLED {event.client_order_id} last_qty={event.last_qty} last_px={event.last_px}",
            )

        def on_order_updated(self, event) -> None:
            self.log.info(
                f"ORDER_UPDATED {event.client_order_id} quantity={event.quantity} price={event.price} trigger_price={event.trigger_price}",
            )

        def on_order_modify_rejected(self, event) -> None:
            self.log.error(
                f"ORDER_MODIFY_REJECTED {event.client_order_id} reason={event.reason}",
            )

    return ParadexSignalStrategyConfig, ParadexSignalStrategy


def _run(args: argparse.Namespace) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    _load_env_file((repo_root / args.env_file).resolve())
    _ensure_paradex_extension(repo_root)

    from nautilus_trader.config import InstrumentProviderConfig, LiveExecEngineConfig, TradingNodeConfig
    from nautilus_trader.live.node import TradingNode
    from nautilus_trader.model.identifiers import InstrumentId
    from nautilus_adapter.adapters.Paradex.config import ParadexDataClientConfig, ParadexExecClientConfig
    from nautilus_adapter.adapters.Paradex.factories import (
        ParadexLiveDataClientFactory,
        ParadexLiveExecClientFactory,
        _build_paradex_http_client,
    )

    backend_cfg = ParadexExecClientConfig(is_testnet=args.testnet)
    backend_client = _build_paradex_http_client(backend_cfg)
    if backend_client is None:
        raise RuntimeError("Failed to build Paradex backend client from env/config")
    if not hasattr(backend_client, "get_orderbook"):
        raise RuntimeError("Paradex backend client missing get_orderbook")

    best_bid, best_ask = _get_reference_prices(
        cast(_ParadexOrderbookClient, backend_client),
        args.symbol,
    )
    plan = _build_runtime_plan(
        side=args.side,
        ref_bid=best_bid,
        ref_ask=best_ask,
        entry_bps=args.entry_bps,
        tp_pct=args.tp_pct,
        sl_pct=args.sl_pct,
    )

    print(
        "Plan:",
        {
            "symbol": args.symbol,
            "side": args.side,
            "quantity": str(args.quantity),
            "best_bid": str(best_bid),
            "best_ask": str(best_ask),
            "entry_price": str(plan.entry_price),
            "tp_price": str(plan.tp_price),
            "sl_trigger_price": str(plan.sl_trigger_price),
        },
    )

    data_cfg = ParadexDataClientConfig(
        is_testnet=args.testnet,
        instrument_provider=InstrumentProviderConfig(load_all=True),
    )
    exec_cfg = ParadexExecClientConfig(
        is_testnet=args.testnet,
        instrument_provider=InstrumentProviderConfig(load_all=True),
        reconciliation_lookback_mins=args.reconciliation_lookback_mins,
        reconciliation_page_size=args.reconciliation_page_size,
    )

    node_cfg = TradingNodeConfig(
        trader_id=args.trader_id,
        exec_engine=LiveExecEngineConfig(
            reconciliation=True,
            reconciliation_lookback_mins=args.reconciliation_lookback_mins,
        ),
        data_clients={"PARADEX": data_cfg},
        exec_clients={"PARADEX": exec_cfg},
    )

    strategy_config_cls, strategy_cls = _build_strategy_classes()
    strategy = strategy_cls(
        strategy_config_cls(
            instrument_id=InstrumentId.from_str(f"{args.symbol}.PARADEX"),
            side=args.side,
            entry_order_type=args.entry_order_type,
            modify_entry_bps=args.modify_entry_bps,
            quantity=args.quantity,
            entry_price=plan.entry_price,
            tp_price=plan.tp_price,
            sl_trigger_price=plan.sl_trigger_price,
            cancel_entry_on_accept=args.cancel_entry_on_accept,
        ),
    )

    node = TradingNode(config=node_cfg)
    node.add_data_client_factory("PARADEX", ParadexLiveDataClientFactory)
    node.add_exec_client_factory("PARADEX", ParadexLiveExecClientFactory)
    node.trader.add_strategy(strategy)
    node.build()

    def _bus_log(msg: object) -> None:
        print(f"BUS_EVENT {type(msg).__name__} {msg}")

    node.kernel.msgbus.subscribe("events.order*", _bus_log)
    node.kernel.msgbus.subscribe("events.position*", _bus_log)

    stop_timer: threading.Timer | None = None
    try:
        stop_timer = threading.Timer(args.runtime_secs, node.stop)
        stop_timer.daemon = True
        stop_timer.start()
        node.run(raise_exception=True)
    finally:
        if stop_timer is not None:
            stop_timer.cancel()
        node.dispose()


def main() -> None:
    args = _parse_args()
    _run(args)


if __name__ == "__main__":
    main()
