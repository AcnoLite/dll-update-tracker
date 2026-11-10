"""Tests for scripts/binaries.py: PE version parsing, zips, Range reads, caching.

All binaries are built in memory; no network access.
"""

import io
import os
import re
import struct
import sys
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import binaries  # noqa: E402


def make_pe(version=(310, 4, 0, 0), with_key=True, padding=0):
    """Build the smallest PE that pe_file_version can read: one .rsrc section."""
    a, b, c, d = version
    rsrc = b""
    if with_key:
        rsrc += b"\0" * 6 + "VS_VERSION_INFO".encode("utf-16-le") + b"\0\0" * 2
    rsrc += struct.pack("<IIIIII", 0xFEEF04BD, 0x00010000, (a << 16) | b, (c << 16) | d, 0, 0)

    pe_offset = 0x40
    section_table = pe_offset + 24
    rsrc_offset = section_table + 40 + padding
    dos = bytearray(64)
    dos[:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, pe_offset)
    coff = b"PE\0\0" + struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, 0, 0)
    section = b".rsrc\0\0\0" + struct.pack("<IIII", len(rsrc), 0x1000, len(rsrc), rsrc_offset) + b"\0" * 16
    return bytes(dos) + coff + section + b"\0" * padding + rsrc


def make_zip(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buf.getvalue()


class PeVersionTest(unittest.TestCase):
    def test_reads_file_version(self):
        self.assertEqual(binaries.pe_file_version(io.BytesIO(make_pe((2, 0, 2, 68)))), "2.0.2.68")

    def test_reads_version_without_utf16_key(self):
        self.assertEqual(binaries.pe_file_version(io.BytesIO(make_pe((1, 2, 3, 4), with_key=False))), "1.2.3.4")

    def test_rejects_non_pe(self):
        with self.assertRaises(binaries.BinaryError):
            binaries.pe_file_version(io.BytesIO(b"version https://git-lfs.github.com/spec/v1\n" + b"\0" * 64))

    def test_missing_version_resource(self):
        pe = bytearray(make_pe())
        sig = pe.find(b"\xbd\x04\xef\xfe")
        pe[sig:sig + 4] = b"\0\0\0\0"
        with self.assertRaises(binaries.BinaryError):
            binaries.pe_file_version(io.BytesIO(bytes(pe)))


class FakeRangeServer:
    """Answers SESSION.get with 206 slices of one in-memory file."""

    def __init__(self, data):
        self.data = data
        self.requests = 0

    def get(self, url, headers=None, **kwargs):
        self.requests += 1
        start, end = map(int, re.match(r"bytes=(\d+)-(\d+)", headers["Range"]).groups())
        resp = mock.Mock()
        resp.status_code = 206
        resp.url = url
        resp.content = self.data[start:end + 1]
        resp.headers = {"Content-Range": f"bytes {start}-{end}/{len(self.data)}"}
        return resp


class RemoteFileTest(unittest.TestCase):
    def test_reads_pe_over_range_requests(self):
        pe = make_pe((310, 9, 16, 0), padding=2_000_000)
        server = FakeRangeServer(pe)
        with mock.patch.object(binaries.net, "SESSION", server):
            raw, f = binaries.open_remote("https://example.test/nvngx_dlss.dll")
            self.assertEqual(binaries.pe_file_version(f), "310.9.16.0")
        # Only the headers and the resource section are read, not the 2 MB of padding.
        self.assertLess(raw.bytes_fetched, 600 * 1024)

    def test_reads_zip_member_over_range_requests(self):
        archive = make_zip({"bin/libxess.dll": make_pe((2, 0, 2, 68)), "readme.txt": b"hi"})
        with mock.patch.object(binaries.net, "SESSION", FakeRangeServer(archive)):
            _, f = binaries.open_remote("https://example.test/sdk.zip")
            found = binaries._versions_from_zip(lambda: f, re.compile(r".*\.dll"), "src", "k1", None)
        self.assertEqual(found["libxess.dll"]["version"], "2.0.2.68")

    def test_server_without_range_support_is_an_error(self):
        resp = mock.Mock(status_code=200)
        resp.raise_for_status.return_value = None
        session = mock.Mock()
        session.get.return_value = resp
        with mock.patch.object(binaries.net, "SESSION", session):
            with self.assertRaises(binaries.BinaryError):
                binaries.RemoteFile("https://example.test/file")


class ZipTest(unittest.TestCase):
    def setUp(self):
        binaries._RUN_CACHE.clear()

    def test_backslash_paths_are_normalised(self):
        archive = make_zip({"bin\\x64\\dxcompiler.dll": make_pe((1, 9, 2609, 0)),
                            "bin\\x86\\dxcompiler.dll": make_pe((1, 9, 2609, 1))})
        found = binaries._versions_from_zip(lambda: io.BytesIO(archive), re.compile(r"bin/x64/.*\.dll"),
                                            "src", "k2", None)
        self.assertEqual(list(found), ["dxcompiler.dll"])
        self.assertEqual(found["dxcompiler.dll"]["version"], "1.9.2609.0")
        self.assertEqual(found["dxcompiler.dll"]["source"], "src:bin/x64/dxcompiler.dll")

    def test_same_archive_is_opened_once_per_run(self):
        archive = make_zip({"bin/x64/sl.reflex.dll": make_pe((2, 14, 16, 0))})
        opens = []

        def opener():
            opens.append(1)
            return io.BytesIO(archive)

        binaries._versions_from_zip(opener, re.compile(r".*\.dll"), "src", "k3", None)
        binaries._versions_from_zip(opener, re.compile(r".*\.dll"), "src", "k3", None)
        self.assertEqual(len(opens), 1)


class FetchDllVersionsTest(unittest.TestCase):
    TREE = {"tree": [
        {"type": "blob", "path": "lib/Windows_x86_64/rel/nvngx_dlss.dll", "sha": "aaa"},
        {"type": "blob", "path": "lib/Windows_x86_64/dev/nvngx_dlss.dll", "sha": "bbb"},
    ]}
    LOCATOR = {"type": "github-file", "repo": "NVIDIA/DLSS", "path_regex": r"lib/Windows_x86_64/rel/.*\.dll"}

    def test_unchanged_blob_is_not_downloaded(self):
        previous = {"nvngx_dlss.dll": {"version": "310.9.16.0", "date": "2026-10-16",
                                       "source": "github-file:x", "key": "blob:aaa"}}
        with mock.patch.object(binaries.net, "github_json", return_value=self.TREE), \
             mock.patch.object(binaries, "_github_file_version", side_effect=AssertionError("downloaded")):
            found, errors = binaries.fetch_dll_versions([self.LOCATOR], previous)
        self.assertEqual(errors, [])
        self.assertEqual(found["nvngx_dlss.dll"]["version"], "310.9.16.0")

    def test_changed_blob_is_read_again(self):
        previous = {"nvngx_dlss.dll": {"version": "310.4.0.0", "key": "blob:old", "source": "github-file:x"}}
        with mock.patch.object(binaries.net, "github_json", side_effect=[self.TREE, [{"commit": {"committer": {"date": "2026-11-01T00:00:00Z"}}}]]), \
             mock.patch.object(binaries, "_github_file_version", return_value=("310.9.16.0", 1024)):
            found, _ = binaries.fetch_dll_versions([self.LOCATOR], previous)
        self.assertEqual(found["nvngx_dlss.dll"]["version"], "310.9.16.0")
        self.assertEqual(found["nvngx_dlss.dll"]["date"], "2026-11-01")
        self.assertEqual(found["nvngx_dlss.dll"]["key"], "blob:aaa")

    def test_failure_keeps_previous_versions(self):
        previous = {"nvngx_dlss.dll": {"version": "310.4.0.0", "key": "blob:old",
                                       "source": "github-file:NVIDIA/DLSS/x"}}
        with mock.patch.object(binaries.net, "github_json", side_effect=RuntimeError("rate limited")):
            found, errors = binaries.fetch_dll_versions([self.LOCATOR], previous)
        self.assertEqual(found["nvngx_dlss.dll"]["version"], "310.4.0.0")
        self.assertEqual(len(errors), 1)
        self.assertIn("rate limited", errors[0])

    def test_no_match_is_reported(self):
        locator = dict(self.LOCATOR, path_regex=r"nothing/.*\.dll")
        with mock.patch.object(binaries.net, "github_json", return_value=self.TREE):
            found, errors = binaries.fetch_dll_versions([locator], {})
        self.assertEqual(found, {})
        self.assertEqual(len(errors), 1)

    def test_unknown_locator_type_is_reported(self):
        found, errors = binaries.fetch_dll_versions([{"type": "ftp"}], {})
        self.assertEqual(found, {})
        self.assertIn("unknown", errors[0])


if __name__ == "__main__":
    unittest.main()
