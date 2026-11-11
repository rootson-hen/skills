import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("findings", Path(__file__).resolve().parents[1] / "scripts/check-findings.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FindingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "raw.md").write_text("raw report")
        self.ref = {"path": "raw.md", "sha256": hashlib.sha256(b"raw report").hexdigest()}
        self.source = {"repository": "example/repo", "base": "a" * 40, "head": "b" * 40, "scope": "whole-feature"}
        self.claim = {"id": "C1", "claim": "Concrete claim", "source": self.source, "disposition": "accepted", "reason": "documented tradeoff",
                      "observations": [{"axis": "Spec", "round": "round-1", "local_id": "P1", "source": self.source, "report": self.ref}]}
        self.ledger = {"schema_version": 1, "source": self.source, "claims": [self.claim]}

    def test_accepted_claim_is_not_an_open_blocker(self):
        self.assertTrue(m.check(self.ledger, self.source, self.base)["accepted"])

    def test_shape_source_open_required_and_references(self):
        for mutate in (lambda l: l["claims"][0].update(disposition="required"),
                       lambda l: l["claims"][0].update(reason=""),
                       lambda l: l.update(source={"head": "old"}),
                       lambda l: l["claims"][0]["observations"][0].update(axis="Merged"),
                       lambda l: l["claims"][0]["observations"][0].update(report={"path": "absent", "sha256": "x"}),
                       lambda l: l["claims"][0].update(duplicate_of="C1")):
            ledger = copy.deepcopy(self.ledger)
            mutate(ledger)
            with self.assertRaises(ValueError):
                m.check(ledger, self.source, self.base)

    def test_fixed_needs_current_verification(self):
        self.claim.update(disposition="fixed", repair={"commit": "c" * 40})
        with self.assertRaises(ValueError):
            m.check(self.ledger, self.source, self.base)
        self.claim["verification"] = {"source": self.source, "outcome": "passed", "evidence": self.ref}
        self.assertTrue(m.check(self.ledger, self.source, self.base)["accepted"])

    def test_duplicate_observations_remain_separate(self):
        second = copy.deepcopy(self.claim)
        second.update(id="C2", duplicate_of="C1")
        second["observations"][0].update(axis="Standards", local_id="S1")
        self.ledger["claims"].append(second)
        self.assertEqual(m.check(self.ledger, self.source, self.base)["claims"], 2)


if __name__ == "__main__":
    unittest.main()
