"""Regression tests for scripts/fetch_versions.py. Network calls are mocked.

Run with: python -m unittest discover -s tests
"""

import json
import os
import shutil
import sys
import tempfile
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
        with mock.patch.object(fv.net.SESSION, "get", return_value=fake_response(releases)):
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
        with mock.patch.object(fv.net.SESSION, "get", return_value=fake_response(index)), \
             mock.patch.object(fv, "_get_nuget_date", return_value=None):
            stable, pre = fv.fetch_nuget_versions("Some.Package")
        self.assertEqual(stable["version"], "1.2.0")
        self.assertIsNone(pre)

    def test_prerelease_newer_than_stable_is_kept(self):
        index = {"versions": ["1.2.0", "1.3.0-preview2", "1.3.0-preview3"]}
        with mock.patch.object(fv.net.SESSION, "get", return_value=fake_response(index)), \
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


class ParseVersionTest(unittest.TestCase):
    def test_tag_prefixes_are_stripped(self):
        self.assertEqual(fv.parse_version("v1.2.3"), "1.2.3")
        self.assertEqual(fv.parse_version("release-3.4.20"), "3.4.20")
        self.assertEqual(fv.parse_version("RELEASE_20200207"), "RELEASE_20200207")
        self.assertEqual(fv.parse_version("2.0-beta.20"), "2.0-beta.20")


class GithubTagsTest(unittest.TestCase):
    def test_highest_version_wins_over_alphabetical_order(self):
        refs = [{"ref": f"refs/tags/{t}"} for t in ["3.10.0", "3.4.2-bsd", "3.9.1", "4.0.0", "nightly"]]
        commit = {"commit": {"committer": {"date": "2019-01-07T10:00:00Z"}}}
        with mock.patch.object(fv.net, "github_json", side_effect=[refs, commit]) as api:
            stable, pre = fv.fetch_github_tags("NVIDIAGameWorks/PhysX")
        self.assertEqual(stable, {"version": "4.0.0", "date": "2019-01-07"})
        self.assertIsNone(pre)
        self.assertEqual(api.call_args_list[1].args[0], "/repos/NVIDIAGameWorks/PhysX/commits/4.0.0")

    def test_prerelease_tag_kept_only_when_higher(self):
        refs = [{"ref": f"refs/tags/{t}"} for t in ["v1.0.0", "v1.1.0-rc1", "v0.9.0-beta"]]
        commit = {"commit": {"committer": {"date": "2026-01-01T00:00:00Z"}}}
        with mock.patch.object(fv.net, "github_json", side_effect=[refs, commit, commit]):
            stable, pre = fv.fetch_github_tags("o/r")
        self.assertEqual(stable["version"], "1.0.0")
        self.assertEqual(pre["version"], "1.1.0-rc1")


def commit(sha, message, date):
    return {"sha": sha, "commit": {"message": message, "committer": {"date": date}}}


class GithubCommitsTest(unittest.TestCase):
    COMMITS = [
        commit("f00dbabe1234", "Fix typo", "2026-11-10T05:10:52Z"),
        commit("c0ffee987654", "R620-Developer SDK", "2026-11-01T00:00:00Z"),
    ]

    def test_regex_on_commit_message(self):
        with mock.patch.object(fv.net, "github_json", return_value=self.COMMITS):
            result = fv.fetch_github_commits({"repo": "NVIDIA/nvapi", "regex": r"^(R\d+)"})
        self.assertEqual(result, {"version": "R620", "date": "2026-11-01"})

    def test_rolling_version_without_regex(self):
        with mock.patch.object(fv.net, "github_json", return_value=self.COMMITS):
            result = fv.fetch_github_commits({"repo": "NVIDIA-RTX/NVRHI"})
        self.assertEqual(result, {"version": "f00dbab", "date": "2026-11-10", "rolling": True})

    def test_no_match_returns_none(self):
        with mock.patch.object(fv.net, "github_json", return_value=self.COMMITS):
            self.assertIsNone(fv.fetch_github_commits({"repo": "o/r", "regex": r"^v(\d+)"}))


class SourceDispatchTest(unittest.TestCase):
    def test_incomplete_or_unknown_source_is_reported(self):
        entry = {"sources": [{"type": "github"}, {"type": "ftp", "url": "ftp://x"}]}
        stable, _, active, errors = fv.fetch_entry(entry)
        self.assertIsNone(stable)
        self.assertIsNone(active)
        self.assertEqual(len(errors), 2)
        self.assertIn("unknown or incomplete source", errors[0])

    def test_scrapling_is_not_imported_until_an_html_source_runs(self):
        # PEP 810 lazy import: importing the fetcher must not load the browser stack.
        self.assertNotIn("scrapling", sys.modules)


class FetchEntryErrorsTest(unittest.TestCase):
    def test_failing_sources_are_reported(self):
        entry = {"sources": [{"type": "github", "repo": "a/b"}, {"type": "nuget", "package_id": "P"}]}
        with mock.patch.object(fv.net.SESSION, "get", side_effect=RuntimeError("rate limited")):
            stable, pre, active, errors = fv.fetch_entry(entry)
        self.assertIsNone(stable)
        self.assertIsNone(active)
        self.assertEqual(len(errors), 2)
        self.assertIn("rate limited", errors[0])

    def test_fallback_success_keeps_earlier_errors(self):
        entry = {"sources": [{"type": "scraping-json", "url": "https://x/a.json", "json_path": "v"},
                             {"type": "scraping-json", "url": "https://x/b.json", "json_path": "v"}]}
        responses = [RuntimeError("boom"), fake_response({"v": "1.2.3"})]
        with mock.patch.object(fv.net.SESSION, "get", side_effect=responses):
            stable, _, active, errors = fv.fetch_entry(entry)
        self.assertEqual(stable["version"], "1.2.3")
        self.assertEqual(active, "scraping-json:https://x/b.json")
        self.assertEqual(len(errors), 1)


class MainExitCodeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "tracker.json")
        tracker = {
            "_meta": {"last_updated": "2026-01-01"},
            "entries": [
                {"id": "a", "sources": [{"type": "nuget", "package_id": "A"}],
                 "versions": {"stable": {"version": "1.0", "date": None}, "prerelease": None},
                 "last_checked": "2026-01-01"},
                {"id": "b", "sources": [{"type": "nuget", "package_id": "B"}],
                 "versions": {"stable": {"version": "2.0", "date": None}, "prerelease": None},
                 "last_checked": "2026-01-01"},
                {"id": "m", "manual": True, "sources": [], "versions": {}, "last_checked": None},
            ],
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(tracker, f)
        patcher = mock.patch.object(fv, "TRACKER_PATH", self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp)

    def run_main(self, nuget_side_effect):
        with mock.patch.object(fv, "fetch_nuget_versions", side_effect=nuget_side_effect), \
             mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            code = fv.main()
        with open(self.path, encoding="utf-8") as f:
            return code, {e["id"]: e for e in json.load(f)["entries"]}

    def test_every_entry_failing_exits_1(self):
        code, entries = self.run_main(RuntimeError("outage"))
        self.assertEqual(code, 1)
        self.assertEqual(entries["a"]["last_checked"], "2026-01-01")
        self.assertEqual(entries["a"]["versions"]["stable"]["version"], "1.0")

    def test_partial_failure_exits_0_and_keeps_failed_entry_untouched(self):
        def nuget(package_id):
            if package_id == "A":
                return {"version": "1.1", "date": None}, None
            raise RuntimeError("404")

        code, entries = self.run_main(nuget)
        self.assertEqual(code, 0)
        self.assertEqual(entries["a"]["versions"]["stable"]["version"], "1.1")
        self.assertNotEqual(entries["a"]["last_checked"], "2026-01-01")
        self.assertEqual(entries["b"]["last_checked"], "2026-01-01")

    def test_dll_failure_is_a_warning_not_a_failure(self):
        with open(self.path, encoding="utf-8") as f:
            tracker = json.load(f)
        tracker["entries"][0]["binaries"] = [{"type": "github-file", "repo": "o/r", "path_regex": ".*"}]
        tracker["entries"][0]["dll_versions"] = {"a.dll": {"version": "1.0.0.0", "key": "k", "source": "github-file:o/r/a.dll"}}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(tracker, f)

        with mock.patch.object(fv.binaries.net, "github_json", side_effect=RuntimeError("tree failed")):
            code, entries = self.run_main(lambda package_id: ({"version": "9", "date": None}, None))
        self.assertEqual(code, 0)
        self.assertEqual(entries["a"]["dll_versions"]["a.dll"]["version"], "1.0.0.0")

    def test_dll_versions_are_stored(self):
        with open(self.path, encoding="utf-8") as f:
            tracker = json.load(f)
        tracker["entries"][1]["binaries"] = [{"type": "nuget", "package_id": "B", "path_regex": ".*"}]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(tracker, f)

        found = {"b.dll": {"version": "2.0.1.0", "date": None, "source": "nuget:B/2.0:b.dll", "key": "nuget:b:2.0"}}
        with mock.patch.object(fv.binaries, "fetch_dll_versions", return_value=(found, [])):
            code, entries = self.run_main(lambda package_id: ({"version": "2.0", "date": None}, None))
        self.assertEqual(code, 0)
        self.assertEqual(entries["b"]["dll_versions"], found)


if __name__ == "__main__":
    unittest.main()
