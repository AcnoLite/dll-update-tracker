"""Shared HTTP session for every fetcher.

One session gives connection reuse (many small Range requests hit the same
hosts) and a single retry policy for transient failures: rate limits (429)
and server errors (5xx) are retried with exponential backoff.
"""

import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GITHUB_API = "https://api.github.com"
TIMEOUT = 30
USER_AGENT = "dll-update-tracker (+https://github.com/AcnoLite/dll-update-tracker)"


def _build_session():
    retry = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=8)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = USER_AGENT
    return session


SESSION = _build_session()


def github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_json(url, params=None, headers=None):
    resp = SESSION.get(url, params=params, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def github_json(path, params=None):
    """GET a GitHub REST API path ("/repos/o/r/releases") with auth if available."""
    return get_json(f"{GITHUB_API}{path}", params=params, headers=github_headers())
