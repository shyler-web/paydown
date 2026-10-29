"""Offline tests for the pure helpers behind repo-memory bootstrapping."""

from __future__ import annotations

import unittest

from app.repo_memory import _band, _domain_for, _required_level, repo_tenant


class RepoTenantTests(unittest.TestCase):
    def test_tenant_id_is_repo_scoped(self) -> None:
        self.assertEqual(repo_tenant("requests"), "repo-requests")

    def test_domain_is_top_level_directory(self) -> None:
        self.assertEqual(_domain_for("src/requests/models.py"), "src")
        self.assertEqual(_domain_for("setup.py"), "root")

    def test_required_level_increases_with_debt(self) -> None:
        self.assertEqual(_required_level(0), 0)
        self.assertEqual(_required_level(12), 1)
        self.assertEqual(_required_level(30), 2)
        self.assertEqual(_required_level(45), 3)
        self.assertEqual(_required_level(60), 4)
        self.assertEqual(_required_level(95), 5)

    def test_band_is_monotonic(self) -> None:
        self.assertEqual(_band(0), "Very clear")
        self.assertEqual(_band(95), "Very hard to follow")


if __name__ == "__main__":
    unittest.main()
