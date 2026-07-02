"""Export the FastAPI OpenAPI schema to frontend/openapi.json.

The checked-in schema file is the contract the frontend generates its types
from (openapi-typescript -> src/lib/api/schema.d.ts). The export is
deterministic (sorted keys, fixed indent) so regeneration is byte-stable and
the ci freshness gate can diff it: a backend model change that is not
re-exported and re-generated fails ci instead of drifting silently.

Run from the repo root::

    uv run python scripts/export_openapi.py
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.main import app

OUT = Path(__file__).resolve().parent.parent / "frontend" / "openapi.json"


def main() -> None:
    """Write the app's OpenAPI schema to the frontend contract file."""
    OUT.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
