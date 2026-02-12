# AUTH-SCRAPER KNOWLEDGE BASE

## OVERVIEW
`builder/auth-scraper/` is a standalone auth/connectivity utility project for exchange login verification, schema extraction, and environment validation.

## STRUCTURE
```
builder/auth-scraper/
├── src/                   # Stable core logic (auth_builders, public_clients, dex_config)
├── tools/                 # CLI-style utility scripts (check/demo/probe/scrape)
├── tests/                 # Unit + integration tests
├── config/                # Canonical env schema output
├── env_example/           # Safe example env files per exchange
├── temp_*_pkg/            # Temporary extracted vendor SDKs
└── venv/                  # Local virtual environment
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Auth signature logic | `builder/auth-scraper/src/auth_builders.py` | exchange-specific signing helpers |
| Public connectivity checks | `builder/auth-scraper/src/public_clients.py` | smoke-level HTTP probes |
| Env/schema validation | `builder/auth-scraper/src/dex_config.py` | schema + env binding |
| Generate canonical schema | `builder/auth-scraper/tools/scrape_to_schema.py` | docs -> JSON schema |
| Run local verification | `builder/auth-scraper/Makefile` | `schema`, `test`, `test-integration` |

## CONVENTIONS
- Keep `src/` as source-of-truth; `tools/` consumes it.
- Integration tests require real credentials and network access.
- Exchange env var naming is uppercase-prefixed per venue.

## ANTI-PATTERNS
- Do not document `venv/` or `temp_*_pkg/` as product code.
- Do not commit local debug outputs/tokens.
- Do not assume auth patterns are interchangeable across exchanges.
