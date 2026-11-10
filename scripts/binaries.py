"""Read the file version of DLLs straight from the published binaries.

SDK release numbers do not tell which version each DLL carries (DLSS ships
nvngx_dlss.dll, nvngx_dlssg.dll and nvngx_dlssd.dll with their own
versions). This module reads the VS_FIXEDFILEINFO block from each DLL's
resources, wherever the vendor publishes it:

- ``github-file``: DLLs committed to a GitHub repository
- ``github-release-asset``: DLLs inside a zip (or .nupkg) attached to the latest release
- ``nuget``: DLLs inside the latest stable NuGet package
- ``url-archive``: DLLs inside a zip at a vendor URL; ``{version}`` in the URL
  is replaced by the entry's stable version (RenderDoc publishes
  ``renderdoc.org/stable/{version}/RenderDoc_{version}_64.zip``)

Everything is read with HTTP Range requests, so only the PE headers and the
resource section are downloaded (a few dozen KB out of a 60 MB DLL). Inside
a zip, only the matching members are downloaded.

Each result carries a ``key`` (blob sha, asset id, package version). When the
key has not changed since the previous run, the stored version is reused
and nothing is downloaded.
"""

import email.utils
import io
import posixpath
import re
import struct
import sys
import zipfile

import net

BUFFER_SIZE = 256 * 1024
MAX_RSRC_SIZE = 32 * 1024 * 1024
NUGET_API = "https://api.nuget.org/v3-flatcontainer"

VS_FIXEDFILEINFO_SIGNATURE = b"\xbd\x04\xef\xfe"
VS_VERSION_INFO_KEY = "VS_VERSION_INFO".encode("utf-16-le")
LFS_POINTER_PREFIX = b"version https://git-lfs"
PRERELEASE_RE = re.compile(r"-(alpha|beta|preview|rc|dev|nightly|pre)", re.IGNORECASE)


class BinaryError(Exception):
    """A binary could not be located or parsed."""


# ─── Remote file over HTTP Range ─────────────────────────────────

class RemoteFile(io.RawIOBase):
    """Seekable, read-only file backed by HTTP Range requests."""

    def __init__(self, url, headers=None):
        super().__init__()
        self.headers = dict(headers or {})
        self.pos = 0
        self.bytes_fetched = 0
        # Probe one byte: resolves redirects (release assets point to signed
        # URLs) and returns the total size in Content-Range.
        resp = net.SESSION.get(url, headers={**self.headers, "Range": "bytes=0-0"},
                               timeout=net.TIMEOUT, allow_redirects=True)
        if resp.status_code != 206:
            resp.raise_for_status()
            raise BinaryError(f"{url} does not support range requests (HTTP {resp.status_code})")
        content_range = resp.headers.get("Content-Range", "")
        match = re.prefixmatch(r"bytes \d+-\d+/(\d+)", content_range)
        if not match:
            raise BinaryError(f"{url}: unexpected Content-Range {content_range!r}")
        self.size = int(match.group(1))
        self.url = resp.url
        self.last_modified = _http_date(resp.headers.get("Last-Modified"))

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        match whence:
            case io.SEEK_SET:
                self.pos = offset
            case io.SEEK_CUR:
                self.pos += offset
            case io.SEEK_END:
                self.pos = self.size + offset
            case _:
                raise ValueError(f"invalid whence {whence}")
        if self.pos < 0:
            raise ValueError("negative seek position")
        return self.pos

    def readinto(self, buffer):
        if self.pos >= self.size or len(buffer) == 0:
            return 0
        end = min(self.pos + len(buffer), self.size) - 1
        resp = net.SESSION.get(self.url, headers={**self.headers, "Range": f"bytes={self.pos}-{end}"},
                               timeout=net.TIMEOUT)
        if resp.status_code != 206:
            resp.raise_for_status()
            raise BinaryError(f"range request ignored (HTTP {resp.status_code})")
        data = resp.content
        buffer[:len(data)] = data
        self.pos += len(data)
        self.bytes_fetched += len(data)
        return len(data)


def _http_date(value):
    """"Tue, 15 Apr 2025 10:00:00 GMT" -> "2025-04-15"; None when absent or invalid."""
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(value).strftime("%Y-%m-%d")
    except TypeError, ValueError:
        return None


def remote_pe_version(url):
    """File version of a remote PE (DLL or installer EXE), read over HTTP Range.

    Returns {"version", "date"}; the date is the server's Last-Modified, if any.
    """
    raw, f = open_remote(url)
    version = pe_file_version(f)
    print(f"    [pe] {url} = {version} ({raw.bytes_fetched // 1024} KB read)", file=sys.stderr)
    return {"version": version, "date": raw.last_modified}


def open_remote(url, headers=None):
    raw = RemoteFile(url, headers=headers)
    return raw, io.BufferedReader(raw, buffer_size=BUFFER_SIZE)


class _LazyRemote:
    """Opens the remote file on first use only, so a fully cached archive costs no request."""

    def __init__(self, url):
        self.url = url
        self.raw = None
        self.file = None

    def open(self):
        if self.file is None:
            self.raw, self.file = open_remote(self.url)
        return self.file

    @property
    def bytes_fetched(self):
        return self.raw.bytes_fetched if self.raw else 0


# ─── PE version resource ─────────────────────────────────────────

def _read_exact(f, offset, size):
    f.seek(offset)
    data = f.read(size)
    if len(data) != size:
        raise BinaryError("truncated PE file")
    return data


def parse_fixed_file_info(data):
    """Return "a.b.c.d" from the VS_FIXEDFILEINFO found in resource bytes, or None."""
    start = data.find(VS_VERSION_INFO_KEY)
    search_from = start if start >= 0 else 0
    sig = data.find(VS_FIXEDFILEINFO_SIGNATURE, search_from)
    if sig < 0 or sig + 16 > len(data):
        return None
    file_ms, file_ls = struct.unpack_from("<II", data, sig + 8)
    return f"{file_ms >> 16}.{file_ms & 0xFFFF}.{file_ls >> 16}.{file_ls & 0xFFFF}"


def pe_file_version(f):
    """Read the file version of a PE (DLL/EXE) from a seekable file object.

    Reads only the DOS header, the section table and the .rsrc section.
    """
    dos = _read_exact(f, 0, 64)
    if dos[:2] != b"MZ":
        raise BinaryError("not a PE file (missing MZ header)")
    pe_offset = struct.unpack_from("<I", dos, 0x3C)[0]
    coff = _read_exact(f, pe_offset, 24)
    if coff[:4] != b"PE\0\0":
        raise BinaryError("not a PE file (missing PE signature)")
    section_count, = struct.unpack_from("<H", coff, 6)
    optional_size, = struct.unpack_from("<H", coff, 20)
    table = _read_exact(f, pe_offset + 24 + optional_size, 40 * section_count)

    for i in range(section_count):
        header = table[i * 40:(i + 1) * 40]
        name = header[:8].rstrip(b"\0")
        if name != b".rsrc":
            continue
        raw_size, raw_offset = struct.unpack_from("<II", header, 16)
        if raw_size > MAX_RSRC_SIZE:
            raise BinaryError(f".rsrc section too large ({raw_size} bytes)")
        version = parse_fixed_file_info(_read_exact(f, raw_offset, raw_size))
        if version:
            return version
        break
    raise BinaryError("no version resource")


def _version_or_skip(f, label):
    """Version of one DLL, or "" when it has none (some vendor DLLs ship
    without a version resource). One such DLL must not hide its siblings."""
    try:
        return pe_file_version(f)
    except BinaryError as e:
        print(f"    [dll] {label}: skipped ({e})", file=sys.stderr)
        return ""


# ─── Locators ────────────────────────────────────────────────────

def _matcher(locator):
    pattern = locator.get("path_regex")
    if not pattern:
        raise BinaryError(f"{locator.get('type')}: missing path_regex")
    return re.compile(pattern, re.IGNORECASE)


def _record(version, source, key, date=None):
    return {"version": version, "date": date, "source": source, "key": key}


def _github_file_date(repo, path):
    commits = net.github_json(f"/repos/{repo}/commits", params={"path": path, "per_page": 1})
    if commits:
        return commits[0]["commit"]["committer"]["date"][:10]
    return None


def _github_file_version(repo, path):
    url = f"https://raw.githubusercontent.com/{repo}/HEAD/{path}"
    raw, f = open_remote(url)
    head = f.read(len(LFS_POINTER_PREFIX))
    if head.startswith(LFS_POINTER_PREFIX):
        # Stored with Git LFS: the real file is served from media.githubusercontent.com.
        raw, f = open_remote(f"https://media.githubusercontent.com/media/{repo}/HEAD/{path}")
    return _version_or_skip(f, path), raw.bytes_fetched


def fetch_github_files(locator, previous):
    repo = locator["repo"]
    match = _matcher(locator)
    tree = net.github_json(f"/repos/{repo}/git/trees/{locator.get('ref', 'HEAD')}",
                           params={"recursive": "1"})
    if tree.get("truncated"):
        print(f"    [!] {repo}: git tree truncated, some files may be missed", file=sys.stderr)

    found = {}
    for item in tree.get("tree", []):
        if item.get("type") != "blob" or not match.fullmatch(item["path"]):
            continue
        name = posixpath.basename(item["path"])
        if name in found:
            continue
        key = f"blob:{item['sha']}"
        source = f"github-file:{repo}/{item['path']}"
        cached = previous.get(name)
        if cached and cached.get("key") == key:
            found[name] = cached
            continue
        version, fetched = _github_file_version(repo, item["path"])
        if not version:
            continue
        print(f"    [dll] {name} = {version} ({fetched // 1024} KB read)", file=sys.stderr)
        found[name] = _record(version, source, key, _github_file_date(repo, item["path"]))
    return found


# Versions already read during this run, keyed by (archive key, member path).
# Two entries can point at the same archive (Streamline and Reflex both read
# the Streamline SDK zip): the second one costs no download.
_RUN_CACHE = {}


def _versions_from_zip(open_archive, match, source_prefix, key, date):
    """Read the versions of the members matching ``match``.

    ``open_archive`` is only called when a member is not in the run cache.
    Member paths are normalised to forward slashes (some zips use backslashes).
    """
    found = {}
    archive = None
    try:
        names = _RUN_CACHE.get((key, None))
        if names is None:
            archive = zipfile.ZipFile(open_archive())
            names = [i.filename for i in archive.infolist() if not i.is_dir()]
            _RUN_CACHE[(key, None)] = names
        for filename in names:
            path = filename.replace("\\", "/")
            if not match.fullmatch(path):
                continue
            name = posixpath.basename(path)
            if name in found:
                continue
            version = _RUN_CACHE.get((key, filename))
            if version is None:
                if archive is None:
                    archive = zipfile.ZipFile(open_archive())
                # ZipExtFile is seekable: moving forward decompresses without
                # keeping the whole member in memory.
                with archive.open(filename) as member:
                    version = _version_or_skip(member, path)
                _RUN_CACHE[(key, filename)] = version
            if version:
                found[name] = _record(version, f"{source_prefix}:{path}", key, date)
    finally:
        if archive is not None:
            archive.close()
    return found


def _reuse_if_unchanged(previous, key):
    cached = {name: rec for name, rec in previous.items() if rec.get("key") == key}
    return cached or None


def fetch_release_asset(locator, previous):
    repo = locator["repo"]
    match = _matcher(locator)
    asset_re = re.compile(locator["asset_regex"], re.IGNORECASE)
    release = net.github_json(f"/repos/{repo}/releases/latest")
    asset = next((a for a in release.get("assets", []) if asset_re.fullmatch(a["name"])), None)
    if asset is None:
        raise BinaryError(f"{repo} {release.get('tag_name')}: no asset matches {locator['asset_regex']}")

    key = f"asset:{asset['id']}:{asset.get('updated_at', '')}"
    cached = _reuse_if_unchanged(previous, key)
    if cached:
        return cached

    date = (release.get("published_at") or "")[:10] or None
    remote = _LazyRemote(asset["browser_download_url"])
    found = _versions_from_zip(remote.open, match, f"github-release-asset:{repo}/{asset['name']}", key, date)
    print(f"    [dll] {asset['name']}: {len(found)} DLL(s), {remote.bytes_fetched // 1024} KB read",
          file=sys.stderr)
    return found


def latest_nuget_stable(package_id):
    index = net.get_json(f"{NUGET_API}/{package_id.lower()}/index.json")
    for version in reversed(index.get("versions", [])):
        if not PRERELEASE_RE.search(version):
            return version
    return None


def fetch_nuget_package(locator, previous):
    package_id = locator["package_id"]
    match = _matcher(locator)
    version = latest_nuget_stable(package_id)
    if not version:
        raise BinaryError(f"{package_id}: no stable version on NuGet")

    key = f"nuget:{package_id.lower()}:{version}"
    cached = _reuse_if_unchanged(previous, key)
    if cached:
        return cached

    pid = package_id.lower()
    remote = _LazyRemote(f"{NUGET_API}/{pid}/{version.lower()}/{pid}.{version.lower()}.nupkg")
    found = _versions_from_zip(remote.open, match, f"nuget:{package_id}/{version}", key, None)
    print(f"    [dll] {package_id} {version}: {len(found)} DLL(s), {remote.bytes_fetched // 1024} KB read",
          file=sys.stderr)
    return found


def fetch_url_archive(locator, previous):
    url = locator["url"]
    match = _matcher(locator)
    key = f"url:{url}"
    cached = _reuse_if_unchanged(previous, key)
    if cached:
        return cached

    remote = _LazyRemote(url)
    found = _versions_from_zip(remote.open, match, f"url-archive:{url}", key, None)
    # The vendor's Last-Modified is the closest thing to a release date.
    date = remote.raw.last_modified if remote.raw else None
    for record in found.values():
        record["date"] = date
    print(f"    [dll] {url}: {len(found)} DLL(s), {remote.bytes_fetched // 1024} KB read", file=sys.stderr)
    return found


LOCATORS = frozendict({
    "github-file": fetch_github_files,
    "github-release-asset": fetch_release_asset,
    "nuget": fetch_nuget_package,
    "url-archive": fetch_url_archive,
})


def fetch_dll_versions(locators, previous=None, version=None):
    """Resolve every locator of an entry.

    ``version`` is the entry's stable version, substituted for ``{version}``
    in locator URLs. Returns (dll_versions, errors). dll_versions maps a DLL
    file name to its record. A locator that fails keeps the DLLs it produced
    last time, so a transient error never erases known versions.
    """
    previous = previous or {}
    result = {}
    errors = []
    for locator in locators:
        kind = locator.get("type")
        handler = LOCATORS.get(kind)
        try:
            if handler is None:
                raise BinaryError(f"unknown binary locator type {kind!r}")
            if "{version}" in locator.get("url", ""):
                if not version:
                    raise BinaryError("URL needs {version} but the entry has no stable version")
                locator = locator | {"url": locator["url"].replace("{version}", version)}
            found = handler(locator, previous)
            if not found:
                raise BinaryError(f"{kind}: no file matches {locator.get('path_regex')}")
        except Exception as e:  # noqa: BLE001 - every failure is reported, none is fatal
            errors.append(f"binary {kind}: {e}")
            print(f"    [!] binary {kind} failed: {e}", file=sys.stderr)
            prefix = f"{kind}:"
            found = {n: r for n, r in previous.items() if str(r.get("source", "")).startswith(prefix)}
        for name, record in found.items():
            result.setdefault(name, record)
    return result, errors
