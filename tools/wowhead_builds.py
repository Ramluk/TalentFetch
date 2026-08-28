"""Discover current Blizzard-compatible talent builds from Wowhead guides.

Wowhead publishes current class-guide builds with Blizzard-compatible talent
payloads. The collector supports both the calculator URL form and the raw
import-code form that Wowhead embeds in guide HTML/JSON.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from build_import_string import validate_import_string

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tools" / "spec_registry.json"
OUTPUT = ROOT / "tools" / "wowhead_builds.json"

HASH_RE = re.compile(
    r"(?:https?://(?:www\.)?wowhead\.com)?/"
    r"(?:[a-z]{2}(?:-[A-Z]{2})?/)?talent-calc/blizzard/"
    r"([A-Za-z0-9+/=_-]{20,})",
    re.I,
)
RAW_IMPORT_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])([A-Za-z0-9+/=_-]{50,140})(?![A-Za-z0-9+/=_-])")
PATCH_RE = re.compile(r"Patch\s+(\d+\.\d+\.\d+)", re.I)
CONTENT_RULES = (
    ("mythic+", ("mythic+", "mythic plus", "mythic-plus", "mythic dungeons")),
    ("raid", ("raid", "single target", "single-target")),
    ("delves", ("delve", "delves")),
    ("pvp", ("pvp", "arena", "battleground")),
    ("leveling", ("leveling", "leveling build", "level 80")),
)
RECOMMENDED_RE = re.compile(r"\b(?:best|current recommendation|current recommendations|recommended)\b", re.I)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(text or "")).strip()


def classify_content(text: str) -> str:
    haystack = normalize(text).lower()
    for content, needles in CONTENT_RULES:
        if any(needle in haystack for needle in needles):
            return content
    return "unknown"


def clean_build_name(text: str, spec_name: str, content: str) -> str:
    text = normalize(text)
    text = re.sub(r"\s*\((?:best|current recommendation)\)\s*", " ", text, flags=re.I)
    if not text:
        return f"{spec_name} {content.title()}" if content != "unknown" else f"{spec_name} build"
    return normalize(text)


class LinkParser(HTMLParser):
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
    CONTEXT_TAGS = {"tr", "li", "td", "th"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []
        self._heading: str = ""
        self._heading_tag: str | None = None
        self._heading_text: list[str] = []
        self._context_depth = 0
        self._context_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.HEADING_TAGS:
            self._heading_tag = tag
            self._heading_text = []
        if tag in self.CONTEXT_TAGS:
            self._context_depth += 1
            if self._context_depth == 1:
                self._context_text = []
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)
        if self._heading_tag is not None:
            self._heading_text.append(data)
        if self._context_depth:
            self._context_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.HEADING_TAGS and self._heading_tag == tag:
            self._heading = normalize(" ".join(self._heading_text))
            self._heading_tag = None
            self._heading_text = []
        if tag == "a" and self._href is not None:
            self.links.append({
                "href": html_lib.unescape(self._href),
                "text": normalize(" ".join(self._text)),
                "heading": self._heading,
                "context": normalize(" ".join(self._context_text)),
            })
            self._href = None
            self._text = []
        if tag in self.CONTEXT_TAGS and self._context_depth:
            self._context_depth -= 1
            if self._context_depth == 0:
                self._context_text = []


def guide_url(spec: dict[str, str]) -> str:
    role_suffix = {"tank": "pve-tank", "healer": "pve-healer", "dps": "pve-dps"}[spec["role"]]
    return f"https://www.wowhead.com/guide/classes/{spec['class']}/{spec['spec']}/talent-builds-{role_suffix}"


def fetch(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "TalentFetch/0.4 (+https://github.com/Ramluk/TalentFetch)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_hashes(text: str) -> list[str]:
    normalized = text.replace("\\\\/", "/").replace("\\/", "/")
    hashes: list[str] = []
    seen: set[str] = set()
    for match in HASH_RE.finditer(normalized):
        value = match.group(1).rstrip(".,);'\"<")
        try:
            validate_import_string(value)
        except ValueError:
            continue
        if value not in seen:
            seen.add(value)
            hashes.append(value)
    return hashes


def extract_raw_imports(text: str) -> list[tuple[str, str]]:
    """Extract raw Blizzard loadout strings with nearby semantic context."""
    normalized = text.replace("\\\\/", "/").replace("\\/", "/")
    results: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in RAW_IMPORT_RE.finditer(normalized):
        value = match.group(1).rstrip(".,);'\"<")
        if value in seen:
            continue
        try:
            validate_import_string(value)
        except ValueError:
            continue
        seen.add(value)
        context = normalize(normalized[max(0, match.start() - 700): match.end() + 700])
        results.append((value, context))
    return results


def discover(spec: dict[str, str], page_html: str) -> list[dict[str, object]]:
    parser = LinkParser()
    parser.feed(page_html)
    results: list[dict[str, object]] = []

    def add_result(talent_hash: str, label: str = "", heading: str = "", context: str = "") -> None:
        try:
            header = validate_import_string(talent_hash)
        except ValueError:
            return
        semantic_context = normalize(f"{label} {heading} {context}")
        content = classify_content(semantic_context)
        results.append({
            "name": clean_build_name(label or heading, spec["name"], content),
            "class": spec["class"],
            "spec": spec["spec"],
            "role": spec["role"],
            "content": content,
            "recommended": bool(RECOMMENDED_RE.search(semantic_context)),
            "source": "wowhead",
            "sourceUrl": guide_url(spec),
            "importString": talent_hash,
            "specId": header.spec_id,
        })

    for link in parser.links:
        for talent_hash in extract_hashes(link["href"]):
            add_result(talent_hash, link["text"], link["heading"], link["context"])

    for talent_hash, context in extract_raw_imports(page_html):
        add_result(talent_hash, "", "", context)

    by_hash: dict[str, dict[str, object]] = {}
    for build in results:
        key = str(build["importString"])
        existing = by_hash.get(key)
        if existing is None:
            by_hash[key] = build
        elif existing["content"] == "unknown" and build["content"] != "unknown":
            by_hash[key] = build
        elif not existing["recommended"] and build["recommended"]:
            existing["recommended"] = True
    return list(by_hash.values())


def extract_patch(page_html: str) -> str | None:
    match = PATCH_RE.search(page_html)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", help="Only collect one spec slug, e.g. warrior/fury")
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument("--strict", action="store_true", help="Fail if any registered spec cannot be collected")
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if args.spec:
        class_slug, spec_slug = args.spec.split("/", 1)
        registry = [x for x in registry if x["class"] == class_slug and x["spec"] == spec_slug]
    builds: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    patches: set[str] = set()
    successful_specs: set[tuple[str, str]] = set()
    for spec in registry:
        url = guide_url(spec)
        try:
            page_html = fetch(url)
            discovered = discover(spec, page_html)
            if discovered:
                successful_specs.add((spec["class"], spec["spec"]))
            builds.extend(discovered)
            patch = extract_patch(page_html)
            if patch:
                patches.add(patch)
            print(f"{spec['name']}: {len(discovered)} builds")
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append({"spec": spec["name"], "url": url, "error": str(exc)})
            print(f"ERROR {spec['name']}: {exc}")
        time.sleep(0.25)

    if not builds:
        raise SystemExit("No Blizzard talent hashes were discovered; refusing to publish empty build data.")

    missing = [spec["name"] for spec in registry if (spec["class"], spec["spec"]) not in successful_specs]
    if args.strict and (errors or missing):
        details = [f"errors={len(errors)}"]
        if missing:
            details.append("missing=" + ", ".join(missing))
        raise SystemExit("Strict Wowhead refresh failed: " + "; ".join(details))

    output = {
        "schemaVersion": 3,
        "generatedAt": int(time.time()),
        "source": "wowhead",
        "patch": sorted(patches)[-1] if patches else None,
        "builds": builds,
        "errors": errors,
    }
    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
