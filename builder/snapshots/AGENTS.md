# SNAPSHOT KNOWLEDGE BASE

## OVERVIEW
`builder/snapshots/` stores committed golden outputs used for regression checks of generated Rust/Python adapter code.

## STRUCTURE
```
builder/snapshots/
└── {exchange}/
    ├── rust/
    └── python/
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Compare generated output | `builder/pipeline/snapshot.py` | byte-level diff against golden files |
| Write/update snapshots | `builder/pipeline/snapshot_write.py` | intentional mutation path |
| Test helper behavior | `builder/tests/snapshot_utils.py` | update-vs-assert test utility |

## CONVENTIONS
- Snapshot trees mirror generated code layout per exchange.
- Use snapshot updates only when intentional generation changes are validated.

## ANTI-PATTERNS
- Do not treat snapshot files as runtime source of truth.
- Do not mutate snapshots in routine CI-style validation flows.
