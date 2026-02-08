from builder.pipeline.models import ExchangeResearch
from builder.pipeline.exceptions import CriticalFieldError

CRITICAL_FIELDS = {
    "exchange_identity": ["venue_id", "exchange_type"],
    "rest_api": ["rest_base_url"],
    "authentication": ["auth_type"],
    "instrument_metadata": ["price_precision", "quantity_precision"],
}


def _fail(path: str):
    raise CriticalFieldError(f"CRITICAL FIELD UNKNOWN: {path}")


def enforce_critical_fields(spec: ExchangeResearch) -> None:
    data = spec.model_dump()

    for section, fields in CRITICAL_FIELDS.items():
        value = data.get(section)

        if value is None:
            _fail(section)

        # list case (e.g. rest_endpoints)
        if isinstance(value, list):
            for i, item in enumerate(value):
                for f in fields:
                    if item.get(f) == "UNKNOWN":
                        _fail(f"{section}[{i}].{f}")
            continue

        # object case
        for f in fields:
            if value.get(f) == "UNKNOWN":
                _fail(f"{section}.{f}")
