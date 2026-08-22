import unittest

from build_import_string import decode_header, normalize_wowhead_blizzard_url, validate_import_string


# Wowhead documents this as a Blizzard-style talent hash. It is intentionally
# kept as a fixture so the collector cannot silently invent a second format.
FIXTURE = "BgQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASCSahAAAAkkAASUIABAAA"


class BuildImportStringTests(unittest.TestCase):
    def test_wowhead_blizzard_hash_is_a_valid_import_payload(self):
        header = decode_header(FIXTURE)
        self.assertGreaterEqual(header.serialization_version, 1)
        self.assertGreater(header.spec_id, 0)
        self.assertEqual(len(header.tree_hash), 16)

    def test_full_wowhead_url_extracts_same_payload(self):
        url = "https://www.wowhead.com/talent-calc/blizzard/" + FIXTURE
        self.assertEqual(normalize_wowhead_blizzard_url(url), FIXTURE)
        self.assertEqual(validate_import_string(FIXTURE).spec_id, decode_header(FIXTURE).spec_id)

    def test_wrong_spec_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_import_string(FIXTURE, expected_spec_id=999999)


if __name__ == "__main__":
    unittest.main()
