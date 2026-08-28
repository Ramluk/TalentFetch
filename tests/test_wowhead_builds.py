import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from wowhead_builds import classify_content, discover, extract_hashes, guide_url


FIXTURE = "BgQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASCSahAAAAkkAASUIABAAA"


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

    def test_classify_content(self):
        self.assertEqual(classify_content("Best Fury Warrior Mythic+ Talent Build"), "mythic+")
        self.assertEqual(classify_content("Best Fury Warrior Raid Talent Build"), "raid")
        self.assertEqual(classify_content("Best Arcane Mage Delves Talent Build"), "delves")
        self.assertEqual(classify_content("Arena talent build"), "pvp")
        self.assertEqual(classify_content("General build"), "unknown")

    def test_extract_hashes_only_accepts_explicit_blizzard_urls(self):
        html = f'<a href="/talent-calc/blizzard/{FIXTURE}">Raid (Best)</a><span>{FIXTURE}</span>'
        self.assertEqual(extract_hashes(html), [FIXTURE])

    def test_raw_extraction_rejects_unrelated_long_strings(self):
        html = '<span>com/images/content/tall-headers/retail/categories/classes-warrior-fury</span>'
        self.assertEqual(discover({"class": "warrior", "spec": "fury", "name": "Fury Warrior", "role": "dps"}, html), [])

    def test_discover_uses_link_label_for_content_and_recommendation(self):
        html = f'''<h2>Talent Import Codes</h2>
            <table><tr>
              <td><a href="/talent-calc/blizzard/{FIXTURE}">Raid (Best)</a></td>
            </tr></table>'''
        spec = {"class": "mage", "spec": "arcane", "name": "Arcane Mage", "role": "dps"}
        builds = discover(spec, html)
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["content"], "raid")
        self.assertTrue(builds[0]["recommended"])
        self.assertEqual(builds[0]["importString"], FIXTURE)
        self.assertGreater(builds[0]["specId"], 0)

    def test_escaped_json_style_urls_are_supported(self):
        html = f'{{"url":"https:\\/\\/www.wowhead.com\\/talent-calc\\/blizzard\\/{FIXTURE}"}}'
        spec = {"class": "mage", "spec": "arcane", "name": "Arcane Mage", "role": "dps"}
        self.assertEqual(extract_hashes(html), [FIXTURE])
        builds = discover(spec, html)
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["importString"], FIXTURE)

    def test_discover_deduplicates_a_build_and_keeps_better_context(self):
        html = f'''
          <a href="/talent-calc/blizzard/{FIXTURE}">Build Import Code Link</a>
          <a href="/talent-calc/blizzard/{FIXTURE}">Raid (Best)</a>
        '''
        spec = {"class": "mage", "spec": "arcane", "name": "Arcane Mage", "role": "dps"}
        builds = discover(spec, html)
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["content"], "raid")
        self.assertTrue(builds[0]["recommended"])


if __name__ == "__main__":
    unittest.main()
