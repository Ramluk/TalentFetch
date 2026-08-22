"""Generate the addon build-data file from the source dataset.

The production pipeline will add a Wowhead adapter that discovers current
Retail builds and resolves Blizzard-compatible talent import strings.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "tools" / "build-data.schema.json"
OUT = ROOT / "addon" / "TalentFetch_Data.lua"


def emit(data: dict) -> None:
    # Keep generated data as a Lua literal. This MVP intentionally does not
    # fetch the network; CI will own the Wowhead source adapter later.
    lines = [
        "-- Generated data file. Do not edit by hand.",
        "TalentFetchBuildData = {",
        f'    patch = {json.dumps(data.get("patch", "unknown"))},',
        f'    generatedAt = {int(data.get("generatedAt", 0))},',
        "    builds = {",
    ]

    for build in data.get("builds", []):
        lines.append("        {")
        for key in ("name", "specID", "heroSpec", "content", "priority", "updatedAt", "importString"):
            if key not in build:
                continue
            value = build[key]
            if isinstance(value, str):
                encoded = json.dumps(value, ensure_ascii=False)
            elif value is None:
                encoded = "nil"
            else:
                encoded = str(value)
            lines.append(f"            {key} = {encoded},")
        lines.append("        },")

    lines.extend(["    },", "}", ""])
    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    emit(json.loads(SCHEMA.read_text(encoding="utf-8")))
