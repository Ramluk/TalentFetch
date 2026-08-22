import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from wowhead_builds import discover, guide_url


def test_guide_url_uses_current_role_suffixes():
    assert guide_url({"class": "warrior", "spec": "fury", "role": "dps", "name": "Fury Warrior"}) == (
        "https://www.wowhead.com/guide/classes/warrior/fury/talent-builds-pve-dps"
    )
    assert guide_url({"class": "paladin", "spec": "protection", "role": "tank", "name": "Protection Paladin"}) == (
        "https://www.wowhead.com/guide/classes/paladin/protection/talent-builds-pve-tank"
    )


def test_discover_extracts_blizzard_hashes_from_anchor_links():
    html = '''
    <a href="/talent-calc/blizzard/ABC123">Mythic+ Dungeons</a>
    <a href="https://www.wowhead.com/talent-calc/blizzard/XYZ789">Raid</a>
    <a href="/talent-calc/blizzard/ABC123">duplicate</a>
    '''
    spec = {"class": "warrior", "spec": "fury", "role": "dps", "name": "Fury Warrior"}
    builds = discover(spec, html)
    assert [b["blizzardHash"] for b in builds] == ["ABC123", "XYZ789"]
    assert builds[0]["source"] == "wowhead"
    assert builds[0]["name"] == "Mythic+ Dungeons"


def test_discover_falls_back_to_raw_html_when_links_are_not_anchors():
    html = '<div data-build="/talent-calc/blizzard/FALLBACK123"></div>'
    spec = {"class": "mage", "spec": "arcane", "role": "dps", "name": "Arcane Mage"}
    builds = discover(spec, html)
    assert len(builds) == 1
    assert builds[0]["blizzardHash"] == "FALLBACK123"
