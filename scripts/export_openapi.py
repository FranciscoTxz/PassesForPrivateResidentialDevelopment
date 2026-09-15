"""Regenerate openapi.json from the FastAPI application.

Usage:
    uv run python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from app import app  # noqa: E402


def main() -> None:
    schema = app.openapi()
    output = ROOT / "openapi.json"
    output.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"openapi.json updated ({len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
