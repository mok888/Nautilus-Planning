# Findings

## Session Summary
Planning context switched from AGENTS hierarchy work to full Lighter adapter implementation (Rust + Python) with Paradex parity target.

## Early Evidence
- Lighter Python runtime still has critical stubs (`pass`) in execution and data clients.
- Existing live tests used auth-scraper/SDK path, not Nautilus adapter runtime path.
- Lighter Rust crate compiles/tests, but no-`reqwest` constraint must be preserved through all edits.

## Constraints to Preserve
- Use hyper-based stack already present in adapters.
- Keep Nautilus lifecycle/reporting semantics in execution/data client methods.
- Prefer in-repo reference implementations over new external patterns.

## Pending Discovery Inputs
- Background parity gap map (`bg_482f4b56`)
- Background Nautilus implementation patterns (`bg_97c4939c`)
- Background compliance checklist (`bg_e976bc41`)

## Implementation Outcomes
- Replaced Lighter Python stub paths with concrete implementations:
  - Added `nautilus-dinger/nautilus_adapter/adapters/Lighter/backend.py` (SDK-backed venue bridge).
  - Reworked `nautilus-dinger/nautilus_adapter/adapters/Lighter/execution.py` to full order lifecycle + report generation + reconciliation.
  - Reworked `nautilus-dinger/nautilus_adapter/adapters/Lighter/data.py` with connect/subscription hooks and instrument publishing.
  - Reworked `nautilus-dinger/nautilus_adapter/adapters/Lighter/providers.py` with async market loading + instrument construction.
  - Reworked `nautilus-dinger/nautilus_adapter/adapters/Lighter/factories.py` to build and inject backend clients.
  - Extended `nautilus-dinger/nautilus_adapter/adapters/Lighter/config.py` with reconciliation settings.

- Improved Rust-side Python interop for Lighter:
  - Replaced `nautilus-dinger/crates/adapters/Lighter/src/python/http.rs` with functional PyO3 client methods for current Rust HTTP API.
  - Updated `nautilus-dinger/crates/adapters/Lighter/src/python/mod.rs` to register bindings.

## Verification Evidence
- `cargo check -p lighter` passed.
- `cargo test -p lighter` passed (13/13).
- `python3 -m pytest tests/test_adapters.py -k Lighter` passed (14 selected tests).
- LSP diagnostics are clean on all changed Lighter Python adapter files.
- No direct `reqwest` usage introduced in adapter crates (scan clean for `nautilus-dinger/crates/adapters/**`).

## Additional Findings (Progressive #1-#4)
- Rust HTTP layer already follows guide: uses `nautilus_network::http::HttpClient` in `nautilus-dinger/crates/adapters/Lighter/src/http/client.rs`.
- Exposed both Python clients:
  - Raw: `PyLighterRawHttpClient`
  - Domain (primary): `PyLighterHttpClient`
  in `nautilus-dinger/crates/adapters/Lighter/src/python/http.rs` and bindings registration.
- Runtime canary execution evidence:
  - Added local SDK environment at `nautilus-dinger/.venv` and installed official package from `elliottech/lighter-python` (`lighter-sdk`).
  - `PYTHONPATH=<.venv site-packages> python3 scripts/lighter_market_canary.py --testnet ...` ran and produced structured report with `submitted=true`, `startup_reconciliation_ok=true`, terminal state `REJECTED`.
  - `PYTHONPATH=<.venv site-packages> python3 scripts/lighter_strategy_runner.py --testnet ...` bootstrapped and connected data path; execution connection failed with venue response `api key not found`.
- Added explicit backend error message for missing Lighter SDK package in `nautilus-dinger/nautilus_adapter/adapters/Lighter/backend.py`.

## Exhaustive Search Findings (Codebase + External)
- Internal pattern mining (`explore` + Grep/AST) identified Paradex parity anchors for terminal-state handling and graceful cancel loops:
  - `nautilus-dinger/scripts/paradex_market_canary.py`
  - `nautilus-dinger/scripts/paradex_strategy_runner.py`
  - `nautilus-dinger/nautilus_adapter/adapters/Paradex/execution.py`
- External research (`librarian`) confirmed official Lighter SDK constraints and flow:
  - order type/time-in-force constants in `elliottech/lighter-python`
  - status querying via active/inactive order endpoints
  - cancel semantics based on order index/client order index usage.
- External research (`librarian`) for aiohttp teardown pointed to deterministic close ordering and explicit nested-session closure; applied in backend close path.

## Final Runtime Outcomes
- Mainnet strategy run now reaches terminal lifecycle events through Nautilus runtime path:
  - `OrderSubmitted` -> `OrderAccepted` -> `OrderCanceled`.
- Mainnet canary achieved compliance pass with terminal state `CANCELED` and report persisted at:
  - `nautilus-dinger/scripts/lighter_market_canary_report_mainnet.json`.

## Stabilization Changes Applied
- Terminal-state hardening:
  - strategy auto-cancel on accept and stop hooks in `nautilus-dinger/scripts/lighter_strategy_runner.py`.
  - market-order submission compatibility fixes in `nautilus-dinger/nautilus_adapter/adapters/Lighter/execution.py`.
  - client-order-index normalization/bounds for venue constraints in `nautilus-dinger/nautilus_adapter/adapters/Lighter/backend.py`.
- Canary robustness:
  - added optional testnet flag pass-through and terminal-state probe scaffolding in `nautilus-dinger/scripts/lighter_market_canary.py`.
  - filtered known non-fatal query-order rate-limit signal from hard-fail classification in `nautilus-dinger/scripts/lighter_market_canary.py`.
- Cleanup robustness:
  - explicit nested API/rest/pool session close sequencing in `nautilus-dinger/nautilus_adapter/adapters/Lighter/backend.py`.
  - unclosed aiohttp session warnings are no longer present on validated strategy shutdown run.

## Paradex-Standard Parity Upgrades (Latest)
- Extended Lighter canary semantics to Paradex-like structure in `nautilus-dinger/scripts/lighter_market_canary.py`:
  - added `entry_client_order_id`, `cancel_rejected`, `cancel_action`, `notes`, `full_soak`, `critical_ok_count`, `terminal_success_count` in reports.
  - added accepted-order terminal probe path with backend cancel/status check.
  - retained robust handling for known non-fatal query-order 429 log noise.
- Extended Lighter execution parity in `nautilus-dinger/nautilus_adapter/adapters/Lighter/execution.py`:
  - added richer status mapping coverage (`OPEN`, `NEW`, `UNTRIGGERED`, `PENDING`, `IN_PROGRESS`).
  - aligned not-found cancellation detection with Paradex-style identifiers (`ORDER_ID_NOT_FOUND`, `CLIENT_ORDER_ID_NOT_FOUND`).
  - implemented conditional modify-order flow (when backend exposes `modify_order`) including retry-on-not-open logic and `generate_order_updated` emission.

## Latest Verification Evidence
- `python3 -m pytest tests/test_adapters.py -k Lighter` passed after parity upgrades.
- Mainnet canary remains compliant after parity upgrades:
  - `compliance_pass=true`, `terminal_state=CANCELED`
  - report: `nautilus-dinger/scripts/lighter_market_canary_report_mainnet.json`.

## Dependency Note
- `reqwest v0.13.2` appears transitively via Nautilus upstream crate `nautilus-network`; not from direct adapter code dependency declarations.
