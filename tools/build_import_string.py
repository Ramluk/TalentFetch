#!/usr/bin/env python3
"""Build Blizzard-compatible talent import strings from Wowhead hashes.

Wowhead's /talent-calc/blizzard/<hash> format uses Blizzard's compact
bit-packed loadout representation. Blizzard's current client defines the
serialization header as 8-bit version, 16-bit spec ID, and 128-bit tree hash,
followed by node state bits. This module deliberately does not invent a
second format: it decodes the Wowhead/Blizzard payload and validates the
header. The WoW client remains the final authority on import validity.
"""

import base64
import re
import struct
from dataclasses import dataclass

_B64_RE = re.compile(r"^[A-Za-z0-9+/=_-]+$")


@dataclass(frozen=True)
class TalentHeader:
    serialization_version: int
    spec_id: int
    tree_hash: bytes
    payload: bytes


def _decode_base64(value: str) -> bytes:
    value = value.strip().replace("-", "+").replace("_", "/")
    value += "=" * ((4 - len(value) % 4) % 4)
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError("Invalid Blizzard talent hash encoding") from exc


def decode_header(value: str) -> TalentHeader:
    """Decode the Blizzard talent serialization header.

    The current Blizzard format is at least 8 + 16 + 128 bits. Bits are
    serialized MSB-first by ExportUtil. The final byte boundary is preserved
    so callers can pass the complete payload through unchanged.
    """
    if not value or not _B64_RE.fullmatch(value.strip()):
        raise ValueError("Talent hash is not a valid base64 payload")

    raw = _decode_base64(value)
    if len(raw) < 19:
        raise ValueError("Talent hash is too short for a Blizzard header")

    # The first 24 bits contain version + spec ID.
    version = raw[0]
    spec_id = int.from_bytes(raw[1:3], "big")
    tree_hash = raw[3:19]
    return TalentHeader(version, spec_id, tree_hash, raw[19:])


def normalize_wowhead_blizzard_url(url: str) -> str:
    """Return the hash portion from a Wowhead Blizzard calculator URL."""
    match = re.search(r"/talent-calc/blizzard/([^/?#]+)", url)
    if not match:
        raise ValueError("Not a Wowhead Blizzard talent calculator URL")
    return match.group(1)


def validate_import_string(value: str, expected_spec_id: int | None = None) -> TalentHeader:
    header = decode_header(value)
    if expected_spec_id is not None and header.spec_id != expected_spec_id:
        raise ValueError(
            f"Talent import is for spec {header.spec_id}, expected {expected_spec_id}"
        )
    return header


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("value", help="Wowhead Blizzard hash or full calculator URL")
    parser.add_argument("--spec-id", type=int)
    args = parser.parse_args()

    value = args.value
    if "/talent-calc/blizzard/" in value:
        value = normalize_wowhead_blizzard_url(value)
    header = validate_import_string(value, args.spec_id)
    print(struct.pack(">BH", header.serialization_version, header.spec_id).hex())
    print(f"serialization_version={header.serialization_version}")
    print(f"spec_id={header.spec_id}")
    print(f"tree_hash={header.tree_hash.hex()}")
    print(f"payload_bytes={len(header.payload)}")
