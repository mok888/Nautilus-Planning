import argparse
import re
import sys
from pathlib import Path


def _latest_entry_triplet_ids(text: str) -> tuple[str, str, str] | None:
    pattern = re.compile(r"BUS_EVENT OrderInitialized .*client_order_id=(O-\d{8}-\d{6}-\d{3}-\d{3}-(\d))")
    matches: list[tuple[str, str]] = pattern.findall(text)
    if not matches:
        return None

    by_prefix: dict[str, dict[str, str]] = {}
    for full_id, leg in matches:
        prefix = full_id.rsplit("-", 1)[0]
        by_prefix.setdefault(prefix, {})[leg] = full_id

    valid_prefixes = [p for p, legs in by_prefix.items() if {"1", "2", "3"}.issubset(set(legs.keys()))]
    if not valid_prefixes:
        return None

    latest_prefix = sorted(valid_prefixes)[-1]
    legs = by_prefix[latest_prefix]
    return legs["1"], legs["2"], legs["3"]


def _count(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text))


def _contains(text: str, pattern: str) -> bool:
    return _count(text, pattern) > 0


def _assert_common(text: str, ids: tuple[str, str, str]) -> list[str]:
    errors: list[str] = []
    if not _contains(text, r"Reconciliation for PARADEX succeeded"):
        errors.append("missing reconciliation success")
    if not _contains(text, r"Startup reconciliation completed"):
        errors.append("missing startup reconciliation completion")
    if _contains(text, r"Failed to generate mass status|Execution state could not be reconciled"):
        errors.append("reconciliation error present")

    for cid in ids:
        if not _contains(text, rf"BUS_EVENT OrderSubmitted .*client_order_id={re.escape(cid)}"):
            errors.append(f"missing submitted event for {cid}")
        if not _contains(text, rf"BUS_EVENT OrderAccepted .*client_order_id={re.escape(cid)}"):
            errors.append(f"missing accepted event for {cid}")
    return errors


def _assert_cancel_mode(text: str, ids: tuple[str, str, str]) -> list[str]:
    errors = _assert_common(text, ids)
    for cid in ids:
        if not _contains(text, rf"BUS_EVENT OrderCanceled .*client_order_id={re.escape(cid)}"):
            errors.append(f"missing canceled event for {cid}")
    if _contains(text, r"ORDER_CANCEL_REJECTED|BUS_EVENT OrderCancelRejected"):
        errors.append("cancel rejected event present")
    return errors


def _assert_market_mode(text: str, ids: tuple[str, str, str]) -> tuple[list[str], list[str]]:
    errors = _assert_common(text, ids)
    warnings: list[str] = []
    entry_id = ids[0]
    has_entry_fill = _contains(text, rf"BUS_EVENT OrderFilled .*client_order_id={re.escape(entry_id)}")
    has_position_evt = _contains(text, r"BUS_EVENT PositionOpened|BUS_EVENT PositionChanged|BUS_EVENT PositionClosed")
    if has_entry_fill and not has_position_evt:
        errors.append("entry fill present but no position lifecycle event")
    if not has_entry_fill:
        warnings.append(f"market entry {entry_id} accepted but no fill observed in runtime window")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--mode", choices=["cancel", "market"], required=True)
    args = parser.parse_args()

    text = Path(args.log).read_text(errors="ignore")
    ids = _latest_entry_triplet_ids(text)
    if ids is None:
        print("ASSERT_FAIL could not find complete latest bracket id triplet")
        return 2

    warnings: list[str] = []
    if args.mode == "cancel":
        errors = _assert_cancel_mode(text, ids)
    else:
        errors, warnings = _assert_market_mode(text, ids)

    if errors:
        print("ASSERT_FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("ASSERT_PASS")
    print(f"entry={ids[0]} sl={ids[1]} tp={ids[2]}")
    for warning in warnings:
        print(f"WARN {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
