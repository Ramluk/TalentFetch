"""Discover and classify Blizzard-compatible talent builds from Wowhead guides."""

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

HASH_RE = re.compile(
    r"(?:https?://www\.wowhead\.com)?/?(?:[a-z]{2}/)?talent-calc/blizzard/([A-Za-z0-9+/=_-]+)",
    re.I,
)
PATCH_RE = re.compile(r"Patch\s+(\d+\.\d+\.\d+)", re.I)

# Ordered from specific to general so "mythic+" wins over generic terms.
CONTENT_RULES = (
    ("mythic+", ("mythic+", "mythic plus", "mythic-plus", "mythic dungeons")),
    ("raid", ("raid", "single target", "single-target")),
    ("delves", ("delve", "delves")),
    ("pvp", ("pvp", "arena", "battleground")),
    ("leveling", ("leveling", "leveling build", "level 80")),
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def classify_content(text: str) -> str:
    haystack = normalize(text).lower()
    for content, needles in CONTENT_RULES:
        if any(needle in haystack for needle in needles):
            return content
    return "unknown"


def clean_build_name(text: str, spec_name: str, content: str) -> str:
    text = normalize(text)
    if not text:
        return f"{spec_name} {content.title()}" if content != "unknown" else f"{spec_name} build"
    text = re.sub(r"\s*\((?:best|current recommendation)\)\s*", " ", text, flags=re.I)
    return normalize(text)


class LinkParser(HTMLParser):
    """Capture talent links plus nearby section-heading context."""

    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []
        self._heading: str | None = None
        self._heading_tag: str | None = None
        self._heading_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.HEADING_TAGS:
            self._heading_tag = tag
            self._heading_text = []
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)
        if self._heading_tag is not None:
            self._heading_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.HEADING_TAGS and self._heading_tag == tag:
            self._heading = normalize(" ".join(self._heading_text))
            self._heading_tag = None
            self._heading_text = []
        if tag == "a" and self._href is not None:
            self.links.append(
                {
                    "href": self._href,
                    "text": normalize(" ".join(self._text)),
                    "heading": self._heading or "",
                }
            )
            self._href = None
            self._text = []


def guide_url(spec: dict[str, str]) -> str:
    role_suffix = {"tank": "pve-tank", "healer": "pve-healer", "dps": "pve-dps"}[spec["role"]]
    return f"https://www.wowhead.com/guide/classes/{spec['class']}/{spec['spec']}/talent-builds-{role_suffix}"


def fetch(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "TalentFetch/0.2 (+https://github.com/Ramluk/TalentFetch)",
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

    def add_result(talent_hash: str, label: str = "", heading: str = "") -> None:
        if talent_hash in seen:
            return
        seen.add(talent_hash)
        context = normalize(f"{label} {heading}")
        content = classify_content(context)
        recommended = bool(re.search(r"\b(?:best|current recommendation|recommended)\b", context, re.I))
        results.append(
            {
                "name": clean_build_name(label or heading, spec["name"], content),
                "class": spec["class"],
                "spec": spec["spec"],
                "role": spec["role"],
                "content": content,
                "recommended": recommended,
                "source": "wowhead",
                "sourceUrl": guide_url(spec),
                "blizzardHash": talent_hash,
            }
        )

    for link in parser.links:
        match = HASH_RE.search(link["href"])
        if match:
            add_result(match.group(1), link["text"], link["heading"])

    # Some Wowhead builds are rendered in non-anchor data. Keep a fallback
    # regex pass so markup changes do not silently produce zero builds.
    if not results:
        for match in HASH_RE.finditer(html):
            add_result(match.group(1))

    return results


def extract_patch(html: str) -> str | None:
    match = PATCH_RE.search(html)
    return match.group(1) if match else None


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
    patches: set[str] = set()
    for spec in registry:
        url = guide_url(spec)
        try:
            html = fetch(url)
            builds.extend(discover(spec, html))
            patch = extract_patch(html)
            if patch:
                patches.add(patch)
            count = sum(1 for b in builds if b["spec"] == spec["spec"] and b["class"] == spec["class"])
            print(f"{spec['name']}: {count} builds")
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append({"spec": spec["name"], "url": url, "error": str(exc)})
            print(f"ERROR {spec['name']}: {exc}")
        time.sleep(0.25)

    output = {
        "schemaVersion": 2,
        "generatedAt": int(time.time()),
        "source": "wowhead",
        "patch": sorted(patches)[-1] if patches else None,
        "builds": builds,
        "errors": errors,
    }
    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not builds:
        raise SystemExit("No Blizzard talent hashes were discovered; refusing to publish empty build data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
