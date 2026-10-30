"""Tests for the demo safety layer and repo-URL allowlist (no network)."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app import security
from app.repos import _validate_repo_url


class SecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        security.reset_for_tests()

    def test_no_access_code_configured_allows(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            security.check_ai_allowed(None)  # must not raise

    def test_access_code_is_enforced(self) -> None:
        with patch.dict(os.environ, {"DEMO_ACCESS_CODE": "s3cret"}, clear=True):
            with self.assertRaises(security.SecurityError) as missing:
                security.check_ai_allowed(None)
            self.assertEqual(missing.exception.status, 403)
            security.check_ai_allowed("s3cret")
            with self.assertRaises(security.SecurityError) as wrong:
                security.check_ai_allowed("wrong")
            self.assertEqual(wrong.exception.status, 403)

    def test_kill_switch(self) -> None:
        with patch.dict(os.environ, {"AI_ENABLED": "false"}, clear=True):
            with self.assertRaises(security.SecurityError) as ctx:
                security.check_ai_allowed()
            self.assertEqual(ctx.exception.status, 503)

    def test_daily_call_budget(self) -> None:
        with patch.dict(os.environ, {"DEMO_MAX_CALLS_PER_DAY": "2"}, clear=True):
            security.check_ai_allowed()
            security.record_ai_call(10)
            security.check_ai_allowed()
            security.record_ai_call(10)
            with self.assertRaises(security.SecurityError) as ctx:
                security.check_ai_allowed()
            self.assertEqual(ctx.exception.status, 429)

    def test_publish_is_off_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(security.publish_enabled())

    def test_usage_reports_limits(self) -> None:
        with patch.dict(os.environ, {"DEMO_MAX_CALLS_PER_DAY": "5"}, clear=True):
            report = security.usage()
        self.assertEqual(report["limits"]["max_calls_per_day"], 5)
        self.assertNotIn("NEBIUS_API_KEY", report)


class RepoUrlTests(unittest.TestCase):
    def test_accepts_public_github_https(self) -> None:
        _validate_repo_url("https://github.com/psf/requests")

    def test_rejects_non_https(self) -> None:
        with self.assertRaises(HTTPException):
            _validate_repo_url("http://github.com/psf/requests")

    def test_rejects_other_hosts(self) -> None:
        with self.assertRaises(HTTPException):
            _validate_repo_url("https://evil.example/psf/requests")

    def test_rejects_credentials_and_extra_paths(self) -> None:
        with self.assertRaises(HTTPException):
            _validate_repo_url("https://user:pass@github.com/psf/requests")
        with self.assertRaises(HTTPException):
            _validate_repo_url("https://github.com/psf/requests/tree/main")


if __name__ == "__main__":
    unittest.main()
