import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from wowhead_builds import discover, guide_url


class WowheadBuildTests(unittest.TestCase):
    def test_guide_url_uses_current_role_suffixes(self):
        self.assertEqual(
            guide_url({"class": "warrior", "spec": "fury", "role": "dps", "name": "Fury Warrior"}),
            "https://www.wowhead.com/guide/classes/warrior/fury/talent-builds-pve-dps",
        )
        self.assertEqual(
            guide_url({"class": "paladin", "spec": "protection", "role": "tank", "name": "Protection Paladin"}),
            "https://www.wowhead.com/guide/classes/paladin/protection/talent-builds-pve-tank",
        )

    def test_discover_extracts_blizzard_hashes_from_anchor_links(self):
        html = '''
        <a href="/talent-calc/blizzard/ABC123">Mythic+ Dungeons</a>
        <a href="https://www.wowhead.com/talent-calc/blizzard/XYZ789">Raid</a>
        <a href="/talent-calc/blizzard/ABC123">duplicate</a>
        '''
        spec = {"class": "warrior", "spec": "fury", "role": "dps", "name": "Fury Warrior"}
        builds = discover(spec, html)
        self.assertEqual([b["blizzardHash"] for b in builds], ["ABC123", "XYZ789"])
        self.assertEqual(builds[0]["source"], "wowhead")
        self.assertEqual(builds[0]["name"], "Mythic+ Dungeons")

    def test_discover_falls_back_to_raw_html_when_links_are_not_anchors(self):
        html = '<div data-build="/talent-calc/blizzard/FALLBACK123"></div>'
        spec = {"class": "mage", "spec": "arcane", "role": "dps", "name": "Arcane Mage"}
        builds = discover(spec, html)
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["blizzardHash"], "FALLBACK123")


if __name__ == "__main__":
    unittest.main()
