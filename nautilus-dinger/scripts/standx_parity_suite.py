import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any

import requests


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-json", default="")
    parser.add_argument("--testnet", action="store_true", default=False)
    parser.add_argument("--runtime-secs", type=int, default=20)
    return parser.parse_args()


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
        if key and (key not in os.environ or not os.environ.get(key)):
            os.environ[key] = value


def _ensure_standx_extension(root: Path) -> None:
    debug_dir = root / "target" / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    so_path = debug_dir / "standx.so"
    lib_path = debug_dir / "libstandx.so"
    if lib_path.exists() and not so_path.exists():
        os.symlink(lib_path.name, so_path)
    if str(debug_dir) not in sys.path:
        sys.path.insert(0, str(debug_dir))


def _build_client(testnet: bool):
    from nautilus_adapter.adapters.StandX.config import StandXExecClientConfig
    from nautilus_adapter.adapters.StandX.factories import _build_standx_http_client

    cfg = StandXExecClientConfig(is_testnet=testnet)
    client = _build_standx_http_client(cfg)
    if client is None:
        raise RuntimeError("failed to build StandX HTTP client")
    return client


def _market_params(base_url: str) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    symbol_info_raw = requests.get(
        f"{base_url}/api/query_symbol_info",
        params={"symbol": "BTC-USD"},
        timeout=20,
    ).json()
    symbol_info = symbol_info_raw[0] if isinstance(symbol_info_raw, list) else symbol_info_raw
    qty_decimals = int(symbol_info.get("qty_tick_decimals", 4))
    price_decimals = int(symbol_info.get("price_tick_decimals", 2))
    min_qty = Decimal(str(symbol_info.get("min_order_qty", "0.0001")))

    px_raw = requests.get(
        f"{base_url}/api/query_symbol_price",
        params={"symbol": "BTC-USD"},
        timeout=20,
    ).json()
    px = px_raw[0] if isinstance(px_raw, list) else px_raw
    mark = Decimal(str(px.get("mark_price") or px.get("price") or px.get("index_price")))

    qty = (Decimal("10") / mark).quantize(Decimal(10) ** -qty_decimals, rounding=ROUND_DOWN)
    if qty < min_qty:
        qty = min_qty

    tick = Decimal(1) / (Decimal(10) ** price_decimals)
    return mark, qty, tick, min_qty


def _submit_limit(client, side: str, qty: Decimal, price: Decimal, tag: str) -> str:
    client_id = f"suite-{tag}-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    client.submit_order(
        "BTC-USD",
        side,
        "LIMIT",
        str(qty),
        str(price),
        client_id,
        "GTC",
        None,
        False,
        None,
    )
    return client_id


def _scenario_submit_cancel(client, base_url: str) -> dict:
    mark, qty, tick, _ = _market_params(base_url)
    buy_price = (mark * Decimal("0.99")).quantize(tick, rounding=ROUND_DOWN)
    cid = _submit_limit(client, "BUY", qty, buy_price, "submit-cancel")
    client.cancel_order_by_client_id(cid, "BTC-USD")
    return {"scenario": "submit_cancel", "ok": True, "client_id": cid}


def _scenario_modify(client, base_url: str) -> dict:
    mark, qty, tick, _ = _market_params(base_url)
    entry_price = (mark * Decimal("0.98")).quantize(tick, rounding=ROUND_DOWN)
    cid = _submit_limit(client, "BUY", qty, entry_price, "modify")

    order = None
    for _ in range(6):
        try:
            order = json.loads(client.get_order_by_client_id(cid))
            break
        except Exception:
            time.sleep(0.4)
    if order is None:
        raise RuntimeError("modify scenario failed to resolve order by client id")
    order_id = str(order.get("order_index") or order.get("order_id") or order.get("id"))
    if not order_id:
        raise RuntimeError("modify scenario failed to resolve order_id")

    modified_price = (entry_price * Decimal("1.001")).quantize(tick, rounding=ROUND_DOWN)
    client.modify_order(
        order_id,
        "BTC-USD",
        "BUY",
        "LIMIT",
        str(qty),
        str(modified_price),
        None,
        None,
    )
    client.cancel_order_by_client_id(cid, "BTC-USD")
    return {
        "scenario": "modify",
        "ok": True,
        "client_id": cid,
        "order_id": order_id,
        "modified_price": str(modified_price),
    }


def _scenario_reconciliation(root: Path, runtime_secs: int, testnet: bool) -> dict:
    cmd = [
        "python3",
        "scripts/standx_strategy_runner.py",
        "--runtime-secs",
        str(runtime_secs),
        "--symbol",
        "BTC-USD-PERP",
        "--side",
        "BUY",
        "--entry-order-type",
        "MARKET",
        "--quantity",
        "0.001",
        "--reconciliation-lookback-mins",
        "20",
        "--reconciliation-page-size",
        "30",
        "--no-cancel-entry-on-accept",
    ]
    if testnet:
        cmd.append("--testnet")

    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=runtime_secs + 120)
    output = (proc.stdout or "") + (proc.stderr or "")
    ok = (
        proc.returncode == 0
        and "Startup reconciliation completed" in output
        and "Failed to generate mass status" not in output
        and "Execution state could not be reconciled" not in output
        and "Traceback" not in output
    )
    return {
        "scenario": "reconciliation",
        "ok": ok,
        "rc": proc.returncode,
        "startup_reconciliation": "Startup reconciliation completed" in output,
        "has_traceback": "Traceback" in output,
    }


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent.parent
    _load_env_file(root / "crates" / "adapters" / "StandX" / "env_standx")
    _ensure_standx_extension(root)

    base_url = os.getenv(
        "STANDX_BASE_URL",
        "https://testnet.perps.standx.com" if args.testnet else "https://perps.standx.com",
    ).rstrip("/")
    client: Any = _build_client(args.testnet)

    results = []
    fatal_error = None
    try:
        results.append(_scenario_submit_cancel(client, base_url))
        results.append(_scenario_modify(client, base_url))
        results.append(_scenario_reconciliation(root, args.runtime_secs, args.testnet))
    except Exception as exc:
        fatal_error = str(exc)

    try:
        client.cancel_all_orders("BTC-USD")
    except Exception:
        pass

    passed = fatal_error is None and all(item.get("ok", False) for item in results)
    report = {
        "suite": "standx_parity",
        "passed": passed,
        "fatal_error": fatal_error,
        "count": len(results),
        "results": results,
    }

    if args.report_json:
        Path(args.report_json).write_text(json.dumps(report, indent=2, sort_keys=True))

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
