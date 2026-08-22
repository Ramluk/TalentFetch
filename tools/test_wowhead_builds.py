import unittest

from wowhead_builds import extract_hashes, extract_raw_imports


FIXTURE = "BgQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASCSahAAAAkkAASUIABAAA"


class WowheadBuildCollectorTests(unittest.TestCase):
    def test_extracts_blizzard_hash_from_calculator_url(self):
        html = f'<a href="https://www.wowhead.com/talent-calc/blizzard/{FIXTURE}">Raid (Best)</a>'
        self.assertEqual(extract_hashes(html), [FIXTURE])

    def test_extracts_raw_import_code_from_guide_markup(self):
        html = f'<div data-build-name="Raid (Best)">{FIXTURE}</div>'
        self.assertEqual(extract_raw_imports(html), [(FIXTURE, html)])

    def test_ignores_unrelated_long_strings(self):
        html = "x" * 100
        self.assertEqual(extract_raw_imports(html), [])


if __name__ == "__main__":
    unittest.main()
