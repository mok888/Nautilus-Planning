import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


@dataclass
class AttemptResult:
    attempt: int
    elapsed_secs: float
    entry_client_order_id: str | None
    terminal_state: str
    reconciliation_ok: bool
    startup_reconciliation_ok: bool
    had_errors: bool
    submitted: bool
    accepted: bool
    filled: bool
    canceled: bool
    rejected: bool
    cancel_rejected: bool
    cancel_action: str | None
    notes: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USD-PERP")
    parser.add_argument("--side", choices=["BUY", "SELL"], default="BUY")
    parser.add_argument("--quantity", default="0.001")
    parser.add_argument("--runtime-secs", type=int, default=30)
    parser.add_argument("--attempt-timeout-secs", type=int, default=120)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--max-total-secs", type=int, default=360)
    parser.add_argument("--reconciliation-lookback-mins", type=int, default=60)
    parser.add_argument("--reconciliation-page-size", type=int, default=50)
    parser.add_argument("--testnet", action="store_true", default=False)
    parser.add_argument("--env-file", default="crates/adapters/StandX/env_standx")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--full-soak", action="store_true", default=False)
    return parser.parse_args()


def _contains(output: str, text: str) -> bool:
    return text in output


def _build_runner_command(args: argparse.Namespace) -> list[str]:
    command = [
        "python3",
        "scripts/standx_strategy_runner.py",
        "--runtime-secs",
        str(args.runtime_secs),
        "--symbol",
        args.symbol,
        "--side",
        args.side,
        "--quantity",
        str(args.quantity),
        "--reconciliation-lookback-mins",
        str(args.reconciliation_lookback_mins),
        "--reconciliation-page-size",
        str(args.reconciliation_page_size),
    ]
    if args.testnet:
        command.append("--testnet")
    return command


def _latest_entry_client_id(output: str) -> str | None:
    lines = [
        line
        for line in output.splitlines()
        if "BUS_EVENT OrderInitialized " in line and "contingency_type=OTO" in line
    ]
    if not lines:
        lines = [line for line in output.splitlines() if "BUS_EVENT OrderInitialized " in line]
    if not lines:
        return None
    last = lines[-1]
    token = "client_order_id="
    start = last.find(token)
    if start < 0:
        return None
    tail = last[start + len(token) :]
    end = tail.find(",")
    if end > 0:
        return tail[:end]

    for pattern in (
        r"BUS_EVENT OrderSubmitted .*client_order_id=([^,\s\)]+)",
        r"ORDER_SUBMITTED\s+([^\s]+)",
    ):
        matches = re.findall(pattern, output)
        if matches:
            return matches[-1]
    return None


def _attempt_once(args: argparse.Namespace, attempt: int) -> AttemptResult:
    started = time.monotonic()
    notes: list[str] = []
    try:
        proc = subprocess.run(
            _build_runner_command(args),
            capture_output=True,
            text=True,
            timeout=args.attempt_timeout_secs,
            check=False,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return AttemptResult(
            attempt=attempt,
            elapsed_secs=time.monotonic() - started,
            entry_client_order_id=None,
            terminal_state="TIMEOUT",
            reconciliation_ok=False,
            startup_reconciliation_ok=False,
            had_errors=True,
            submitted=False,
            accepted=False,
            filled=False,
            canceled=False,
            rejected=False,
            cancel_rejected=False,
            cancel_action=None,
            notes=["runner_timeout"],
        )

    entry_id = _latest_entry_client_id(output)
    submitted = bool(
        entry_id and _contains(output, "BUS_EVENT OrderSubmitted ") and _contains(output, entry_id)
    )
    accepted = bool(
        entry_id and _contains(output, "BUS_EVENT OrderAccepted ") and _contains(output, entry_id)
    )
    filled = bool(
        entry_id and _contains(output, "BUS_EVENT OrderFilled ") and _contains(output, entry_id)
    )
    canceled = bool(
        entry_id and _contains(output, "BUS_EVENT OrderCanceled ") and _contains(output, entry_id)
    )
    rejected = bool(
        entry_id and _contains(output, "BUS_EVENT OrderRejected ") and _contains(output, entry_id)
    )
    cancel_rejected = bool(
        entry_id
        and _contains(output, "BUS_EVENT OrderCancelRejected ")
        and _contains(output, entry_id)
    )

    terminal = "OPEN_OR_UNKNOWN"
    if filled:
        terminal = "FILLED"
    elif canceled:
        terminal = "CANCELED"
    elif rejected:
        terminal = "REJECTED"

    rec_ok = _contains(output, "Reconciliation for STANDX succeeded")
    startup_ok = _contains(output, "Startup reconciliation completed")
    had_errors = any(
        x in output
        for x in [
            "[ERROR]",
            "Failed to generate mass status",
            "Execution state could not be reconciled",
            "Traceback",
        ]
    )

    return AttemptResult(
        attempt=attempt,
        elapsed_secs=time.monotonic() - started,
        entry_client_order_id=entry_id,
        terminal_state=terminal,
        reconciliation_ok=rec_ok,
        startup_reconciliation_ok=startup_ok,
        had_errors=had_errors,
        submitted=submitted,
        accepted=accepted,
        filled=filled,
        canceled=canceled,
        rejected=rejected,
        cancel_rejected=cancel_rejected,
        cancel_action=None,
        notes=notes,
    )


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    _load_env_file((repo_root / args.env_file).resolve())

    started = time.monotonic()
    attempts: list[dict[str, Any]] = []
    final_terminal = "TIMEOUT"
    total_terminal_success = 0
    total_critical_ok = 0

    for i in range(1, args.max_attempts + 1):
        if time.monotonic() - started > args.max_total_secs:
            break
        result = _attempt_once(args, i)
        attempts.append(result.__dict__)

        critical_ok = (
            result.reconciliation_ok
            and result.startup_reconciliation_ok
            and not result.had_errors
            and result.submitted
            and result.accepted
            and not result.rejected
            and (not result.cancel_rejected or result.terminal_state in {"FILLED", "CANCELED"})
        )
        terminal_ok = result.terminal_state in {"FILLED", "CANCELED"}
        if critical_ok:
            total_critical_ok += 1
        if terminal_ok:
            total_terminal_success += 1
        attempts[-1]["critical_ok"] = critical_ok
        attempts[-1]["terminal_ok"] = terminal_ok
        final_terminal = result.terminal_state

        if critical_ok and terminal_ok and not args.full_soak:
            break

    attempts_executed = len(attempts)
    compliance_pass = (
        attempts_executed > 0
        and total_terminal_success == attempts_executed
        and total_critical_ok == attempts_executed
    )

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": args.symbol,
        "side": args.side,
        "mode": "MARKET_CANARY",
        "full_soak": args.full_soak,
        "max_attempts": args.max_attempts,
        "max_total_secs": args.max_total_secs,
        "runtime_secs": args.runtime_secs,
        "attempts_executed": attempts_executed,
        "terminal_success_count": total_terminal_success,
        "critical_ok_count": total_critical_ok,
        "final_terminal_state": final_terminal,
        "compliance_pass": compliance_pass,
        "attempts": attempts,
    }

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True))

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if compliance_pass else 1


if __name__ == "__main__":
    sys.exit(main())
