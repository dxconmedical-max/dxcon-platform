"""Tests for Sprint 010.5 production readiness."""

from __future__ import annotations

import unittest

from scripts.production_readiness_lib import finding, score_findings


class ProductionReadinessLibTests(unittest.TestCase):
    def test_score_findings_all_pass(self):
        findings = [finding("PASS", "a"), finding("PASS", "b")]
        score = score_findings(findings)
        self.assertEqual(score["counts"]["PASS"], 2)
        self.assertEqual(score["score_pct"], 100.0)

    def test_score_findings_with_warning(self):
        findings = [finding("PASS", "a"), finding("WARNING", "b")]
        score = score_findings(findings)
        self.assertEqual(score["score_pct"], 75.0)

    def test_score_findings_with_fail(self):
        findings = [finding("FAIL", "a"), finding("PASS", "b")]
        score = score_findings(findings)
        self.assertEqual(score["counts"]["FAIL"], 1)


if __name__ == "__main__":
    unittest.main()
