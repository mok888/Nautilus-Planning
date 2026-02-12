# PYTHON ADAPTERS KNOWLEDGE BASE

## OVERVIEW
`nautilus-dinger/nautilus_adapter/adapters/` contains per-exchange Python integration layers consumed by NautilusTrader runtime components.

## STRUCTURE
```
nautilus-dinger/nautilus_adapter/adapters/
└── {Exchange}/
    ├── __init__.py
    ├── config.py
    ├── constants.py
    ├── data.py
    ├── execution.py
    ├── factories.py
    └── providers.py
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Adapter config contracts | `.../{Exchange}/config.py` | data/execution client config classes |
| Runtime constants | `.../{Exchange}/constants.py` | venue IDs, URLs, defaults |
| Data-side wiring | `.../{Exchange}/data.py` | market data client/subscription hooks |
| Execution-side wiring | `.../{Exchange}/execution.py` | order lifecycle interfaces |
| Construction boundaries | `.../{Exchange}/factories.py` | client creation and dependency wiring |
| Instrument loading | `.../{Exchange}/providers.py` | instrument provider behavior |

## CONVENTIONS
- Preserve the same file set across exchanges.
- Keep factories responsible for assembly; avoid hidden construction in constants/config.
- Treat `Paradex` as the most complete implementation reference where others are stubs.

## ANTI-PATTERNS
- Do not collapse data and execution concerns into a single adapter module.
- Do not break parity between exchange adapter file layouts.
