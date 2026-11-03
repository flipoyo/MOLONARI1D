"""Offline contract tests, deliberately no remote Git or Omniscience writes."""
import importlib.util
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "twin_registry.py"
SPEC = importlib.util.spec_from_file_location("molo_registry", SCRIPT)
reg = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reg
SPEC.loader.exec_module(reg)


class TwinRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.records = reg.load()

    def test_canonical_git_tree(self):
        with reg.CGS.open("rb") as handle:
            cfg = tomllib.load(handle)
        reg.validate_cgs(cfg)
        self.assertEqual(len(cfg["repos"]), 7)

    def test_root_twin_and_four_poles(self):
        self.assertEqual([r["name"] for r in self.records],
                         ["MOLONARI", *reg.EXPECTED_POLES])

    def test_public_candidate_is_unverified(self):
        doc = reg.public_candidate(self.records)
        self.assertEqual(doc["publication"], "NOT_PUBLISHED")
        self.assertEqual(doc["evidence"], "unverified")
        self.assertFalse(doc["gts_verified"])
        self.assertFalse(doc["glyph_available"])
        self.assertEqual(len(doc["twins"]), 5)
        self.assertTrue(all(len(r["name_sha256"]) == 64 for r in doc["twins"]))

    def test_virtual_lab_and_sampling_point_examples(self):
        examples = SCRIPT.parent / "examples"
        rows = reg.add_examples(self.records,
            [examples / "virtual-lab.toml", examples / "sampling-point.toml"])
        self.assertEqual(rows[-1]["parent"], "LAB-DEMO")
        self.assertEqual(reg.public_candidate(rows)["twins"][-2]["kind"], "virtual-lab")

    def test_duplicate_rejected(self):
        with self.assertRaises(reg.ContractError):
            reg.validate_records(self.records + [self.records[-1]])

    def test_bad_parent_rejected(self):
        with self.assertRaises(reg.ContractError):
            reg.validate_records(self.records + [
                {"name": "SP-X", "kind": "sampling-point",
                 "parent": "MOLO-HRDW", "phase": "example"}
            ])

    def test_legacy_branch_mutation_refused(self):
        with reg.CGS.open("rb") as handle:
            cfg = tomllib.load(handle)
        cfg["repos"][1]["default_branch"] = "CGS-ALPHA"
        with self.assertRaises(reg.ContractError):
            reg.validate_cgs(cfg)

    def test_candidate_stays_unpublished(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "draft.json"
            reg.write_candidate(reg.public_candidate(self.records), str(target))
            self.assertIn('"NOT_PUBLISHED"', target.read_text())


if __name__ == "__main__":
    unittest.main()
