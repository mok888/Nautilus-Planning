# RUST ADAPTERS KNOWLEDGE BASE

## OVERVIEW
`nautilus-dinger/crates/adapters/` holds per-exchange Rust crates with a near-identical module topology.

## STRUCTURE
```
nautilus-dinger/crates/adapters/
└── {Exchange}/
    ├── Cargo.toml
    └── src/
        ├── lib.rs
        ├── common/
        ├── http/
        ├── websocket/
        ├── python/
        ├── data/
        ├── execution/
        └── testing/
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Crate entry + feature gates | `nautilus-dinger/crates/adapters/{Exchange}/src/lib.rs` | module wiring and Python module export |
| Shared models/constants | `.../src/common/` | credential, enums, urls, risk |
| REST behavior | `.../src/http/` | client/signing/query/parse/errors |
| WS behavior | `.../src/websocket/` | handler/messages/parse/errors |
| Python FFI boundary | `.../src/python/` | PyO3 bindings exported to Python layer |

## CONVENTIONS
- Maintain consistent module boundaries across exchanges.
- Keep transport logic in `http/` and `websocket/`, not in `lib.rs`.
- Preserve feature-gated organization (`python`, `data`, `execution`, `test_utils`).

## ANTI-PATTERNS
- Do not introduce one-off crate layouts that diverge from template topology.
- Do not bypass shared `common/` abstractions for exchange constants/models.
