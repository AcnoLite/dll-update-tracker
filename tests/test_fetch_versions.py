"""Regression tests for scripts/fetch_versions.py. Network calls are mocked.

Run with: python -m unittest discover -s tests
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import fetch_versions as fv  # noqa: E402


def fake_response(payload):
    resp = mock.Mock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def release(tag, published, prerelease=False, draft=False):
    return {"tag_name": tag, "published_at": published, "prerelease": prerelease, "draft": draft}


class GithubReleasesTest(unittest.TestCase):
    def fetch(self, releases):
        with mock.patch.object(fv.requests, "get", return_value=fake_response(releases)):
            return fv.fetch_github_releases("owner/repo")

    def test_prerelease_older_than_stable_is_dropped(self):
        # Steam Audio case: the only prerelease predates the latest stable
        # and belongs to a lower version line.
        stable, pre = self.fetch([
            release("v4.8.1", "2026-02-11T00:00:00Z"),
            release("v2.0-beta.20", "2021-04-13T00:00:00Z", prerelease=True),
        ])
        self.assertEqual(stable["version"], "4.8.1")
        self.assertIsNone(pre)

    def test_prerelease_newer_than_stable_is_kept(self):
        stable, pre = self.fetch([
            release("v1.722.0-preview", "2026-10-28T00:00:00Z", prerelease=True),
            release("v1.620.1", "2026-10-20T00:00:00Z"),
        ])
        self.assertEqual(stable["version"], "1.620.1")
        self.assertEqual(pre["version"], "1.722.0-preview")

    def test_older_prerelease_on_a_higher_version_line_is_kept(self):
        # DXC case: 1.10 preview predates a 1.9 stable patch but is still the next line.
        stable, pre = self.fetch([
            release("v1.9.2609", "2026-09-29T00:00:00Z"),
            release("v1.10.2605.37", "2026-08-12T00:00:00Z", prerelease=True),
        ])
        self.assertEqual(stable["version"], "1.9.2609")
        self.assertEqual(pre["version"], "1.10.2605.37")

    def test_tag_without_digits_is_ignored(self):
        # OpenAL Soft case: a "utils" tooling release flagged as prerelease.
        stable, pre = self.fetch([
            release("utils", "2026-11-09T00:00:00Z", prerelease=True),
            release("1.25.2", "2026-05-12T00:00:00Z"),
        ])
        self.assertEqual(stable["version"], "1.25.2")
        self.assertIsNone(pre)

    def test_drafts_are_ignored(self):
        stable, _ = self.fetch([
            release("v9.0.0", "2026-11-01T00:00:00Z", draft=True),
            release("v8.0.0", "2026-10-01T00:00:00Z"),
        ])
        self.assertEqual(stable["version"], "8.0.0")


class NugetTest(unittest.TestCase):
    def test_prerelease_older_than_stable_is_dropped(self):
        index = {"versions": ["1.0.0", "1.1.0-preview1", "1.1.0", "1.2.0"]}
        with mock.patch.object(fv.requests, "get", return_value=fake_response(index)), \
             mock.patch.object(fv, "_get_nuget_date", return_value=None):
            stable, pre = fv.fetch_nuget_versions("Some.Package")
        self.assertEqual(stable["version"], "1.2.0")
        self.assertIsNone(pre)

    def test_prerelease_newer_than_stable_is_kept(self):
        index = {"versions": ["1.2.0", "1.3.0-preview2", "1.3.0-preview3"]}
        with mock.patch.object(fv.requests, "get", return_value=fake_response(index)), \
             mock.patch.object(fv, "_get_nuget_date", return_value=None):
            stable, pre = fv.fetch_nuget_versions("Some.Package")
        self.assertEqual(stable["version"], "1.2.0")
        self.assertEqual(pre["version"], "1.3.0-preview3")


class OutdatedPrereleaseTest(unittest.TestCase):
    def test_missing_dates_keep_the_prerelease(self):
        self.assertFalse(fv.is_outdated_prerelease(
            {"version": "2.0", "date": None}, {"version": "1.0-beta", "date": None}))

    def test_openxr_style_tags_compare_numerically(self):
        self.assertTrue(fv.is_outdated_prerelease(
            {"version": "release-1.1.65", "date": "2026-10-16"},
            {"version": "release-1.0.21", "date": "2022-01-12"}))


if __name__ == "__main__":
    unittest.main()
