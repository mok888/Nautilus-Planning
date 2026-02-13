# Task Plan

## Goal
Fully implement Lighter adapter components in Rust and Python to Paradex-level completeness while preserving Nautilus adapter conventions, using `nautilus_network::http::HttpClient`, and keeping adapter code free of direct `reqwest` usage.

## Scope
- Close all meaningful stub gaps in `nautilus-dinger/crates/adapters/Lighter/` and `nautilus-dinger/nautilus_adapter/adapters/Lighter/`.
- Keep implementation aligned with in-repo patterns (Paradex first, then other mature adapters).
- Validate with Rust + Python checks and explicit dependency guardrails.

## Phases
| Phase | Status | Notes |
|------|--------|-------|
| Planning bootstrap | complete | Catchup run; planning files repointed to Lighter implementation mission |
| Gap mapping | complete | Lighter vs Paradex parity map produced (Python stubs + Rust binding gaps) |
| Python implementation | complete | Backend/execution/data/providers/factories implemented; market data translation verified by tests |
| Rust implementation | complete | HTTP/order parity + signing updates + Raw/Domain Python client exposure |
| Validation | complete | `cargo check/test` + `pytest -k Lighter` + canary CLI checks + runtime smoke evidence |
| Finalization | complete | Findings/progress refreshed with exhaustive search evidence and stable mainnet canary path |

## Progressive #1-#4 Status
1. Adapter-runtime live canary: complete with mainnet credentials (accepted -> canceled terminal path; canary compliance pass observed).
2. Rust HTTP/order parity: complete.
3. Real Rust signing replacement: complete (`jubjub-schnorr` path integrated, tests updated/passing).
4. Market data event translation: complete (Python translation paths and tests passing).

## Paradex-Standard Alignment
- Additional parity pass completed for canary semantics and execution lifecycle handling.
- Lighter canary report model now mirrors Paradex-style observability fields and aggregate criteria.
- Lighter execution flow now includes Paradex-like status/not-found handling and conditional modify retry path.

## Hard Constraints
- No direct `reqwest` usage in adapter crate code.
- Follow Nautilus `LiveExecutionClient` and `LiveMarketDataClient` method contracts.
- No fake/no-op passes for required order lifecycle operations.

## Current Assumption
The target is the Lighter adapter (not Nado/other venues) and parity baseline is Paradex behavior/conventions where applicable.

## Remaining External Dependency
- Venue-side rate limits can intermittently surface in `query_order`; canary now tolerates this known transient when terminal lifecycle is otherwise successful.
