"""Offline tests for the Clarify service (analyze + score-validated proposal)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.clarify import _provisional_validation, analyze_repo, propose_refactor
from app.cognitive_debt import score_python_source

COMPLEX = '''def total(values):
    result = 0
    for value in values:
        if value:
            if value > 0:
                if value % 2 == 0:
                    result += value
                else:
                    result -= value
    return result
'''

FLAT = '''def total(values):
    result = 0
    for value in values:
        if value and value > 0:
            result += value
    return result
'''


class ProvisionalValidationTests(unittest.TestCase):
    def test_scoredrop_is_accepted_but_behavior_unverified(self) -> None:
        before = score_python_source(COMPLEX, "m.py")
        after = score_python_source(FLAT, "m.py")
        report = _provisional_validation(before, after, changed=True)
        self.assertFalse(report["behavior_verified"])
        self.assertIn("checks", report)
        self.assertTrue(report["checks"]["code_changed"])
        self.assertGreaterEqual(report["score_drop"], 0)

    def test_unchanged_code_is_not_accepted(self) -> None:
        risk = score_python_source(COMPLEX, "m.py")
        report = _provisional_validation(risk, risk, changed=False)
        self.assertFalse(report["checks"]["code_changed"])


class AnalyzeTests(unittest.TestCase):
    def test_analyze_ranks_python_and_skips_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text(COMPLEX, encoding="utf-8")
            (root / "test_a.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            with patch("app.clarify.repo_cache_path", return_value=root):
                report = analyze_repo("demo", limit=10)
        paths = [f["path"] for f in report["files"]]
        self.assertIn("a.py", paths)
        self.assertNotIn("test_a.py", paths)
        self.assertEqual(report["repo"], "demo")


class ProposeTests(unittest.TestCase):
    def test_propose_uses_generator_and_returns_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text(COMPLEX, encoding="utf-8")
            proposal = {
                "source": FLAT,
                "summary": "Flattened nested conditionals to reduce control-flow depth.",
                "intent_note": "This flattens the guard so the logic reads top-down instead of nested.",
                "reviewer_question": "Does the flattened guard preserve behaviour for negative values?",
            }
            with patch("app.clarify.repo_cache_path", return_value=root), patch(
                "app.clarify._record_proposal"
            ):
                result = propose_refactor("demo", "a.py", generator=lambda s, u: proposal)
        self.assertFalse(result["behavior_verified"])
        self.assertEqual(result["target"], "a.py")
        self.assertIn("---", result["diff"])
        self.assertIn("+++", result["diff"])
        self.assertIn(result["status"], {"accepted", "rejected"})


if __name__ == "__main__":
    unittest.main()
