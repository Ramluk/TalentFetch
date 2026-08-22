"""Discover Blizzard-compatible talent hashes from current Wowhead guides.

Wowhead's current class guides expose Blizzard-style talent calculator links.
The collector intentionally stores the Blizzard hash instead of attempting to
reimplement Blizzard's talent serialization format.

This is a discovery layer: labels/content classification can be refined as we
learn more about Wowhead's page structure. A build is never invented when no
Blizzard hash is present.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tools" / "spec_registry.json"
OUTPUT = ROOT / "tools" / "wowhead_builds.json"

HASH_RE = re.compile(r"(?:https?://www\.wowhead\.com)?/??(?:[a-z]{2}/)?talent-calc/blizzard/([A-Za-z0-9+/=_-]+)", re.I)
PATCH_RE = re.compile(r"Patch\s+(\d+\.\d+\.\d+)", re.I)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        self._href = dict(attrs).get("href")
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


def guide_url(spec: dict[str, str]) -> str:
    role_suffix = {"tank": "pve-tank", "healer": "pve-healer", "dps": "pve-dps"}[spec["role"]]
    return f"https://www.wowhead.com/guide/classes/{spec['class']}/{spec['spec']}/talent-builds-{role_suffix}"


def fetch(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "TalentFetch/0.1 (+https://github.com/Ramluk/TalentFetch)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def discover(spec: dict[str, str], html: str) -> list[dict[str, object]]:
    parser = LinkParser()
    parser.feed(html)
    results: list[dict[str, object]] = []
    seen: set[str] = set()

    for href, text in parser.links:
        match = HASH_RE.search(href)
        if not match:
            continue
        talent_hash = match.group(1)
        if talent_hash in seen:
            continue
        seen.add(talent_hash)
        results.append(
            {
                "name": text or f"{spec['name']} build",
                "class": spec["class"],
                "spec": spec["spec"],
                "role": spec["role"],
                "content": "unknown",
                "source": "wowhead",
                "sourceUrl": guide_url(spec),
                "blizzardHash": talent_hash,
            }
        )

    # Some Wowhead links are rendered as non-anchor data. Keep a fallback
    # regex pass so a markup change doesn't silently produce zero builds.
    if not results:
        for match in HASH_RE.finditer(html):
            talent_hash = match.group(1)
            if talent_hash in seen:
                continue
            seen.add(talent_hash)
            results.append(
                {
                    "name": f"{spec['name']} build",
                    "class": spec["class"],
                    "spec": spec["spec"],
                    "role": spec["role"],
                    "content": "unknown",
                    "source": "wowhead",
                    "sourceUrl": guide_url(spec),
                    "blizzardHash": talent_hash,
                }
            )

    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", help="Only collect one spec slug, e.g. warrior/fury")
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if args.spec:
        class_slug, spec_slug = args.spec.split("/", 1)
        registry = [x for x in registry if x["class"] == class_slug and x["spec"] == spec_slug]

    builds: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for spec in registry:
        url = guide_url(spec)
        try:
            html = fetch(url)
            builds.extend(discover(spec, html))
            print(f"{spec['name']}: {sum(1 for b in builds if b['spec'] == spec['spec'] and b['class'] == spec['class'])} builds")
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append({"spec": spec["name"], "url": url, "error": str(exc)})
            print(f"ERROR {spec['name']}: {exc}")
        time.sleep(0.25)

    output = {
        "schemaVersion": 1,
        "generatedAt": int(time.time()),
        "source": "wowhead",
        "patch": None,
        "builds": builds,
        "errors": errors,
    }
    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not builds:
        raise SystemExit("No Blizzard talent hashes were discovered; refusing to publish empty build data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
