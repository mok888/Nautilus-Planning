import json
from pathlib import Path

import jsonschema

from tools.scrape_to_schema import canonical_schema_template


def test_generated_schema_is_valid(tmp_path: Path) -> None:
    schema = canonical_schema_template({"test": True}, scrape=False)
    jsonschema.Draft202012Validator.check_schema(schema)

    out = tmp_path / "schema.json"
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(loaded)
