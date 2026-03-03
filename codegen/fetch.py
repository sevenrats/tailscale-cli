"""
Fetch Go source files from GitHub.

Uses the raw.githubusercontent.com endpoint — no GitHub API token needed
for public repos.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error
from functools import lru_cache
from typing import List


def fetch_go_source(repo: str, ref: str, path: str) -> str:
    """
    Download a single file from a GitHub repo at a specific ref.

    Parameters
    ----------
    repo : str   e.g. "tailscale/tailscale"
    ref  : str   commit SHA or tag, e.g. "v1.82.0" or "abc123…"
    path : str   path inside the repo, e.g. "ipn/ipnstate/ipnstate.go"
    """
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "tailscale-cli-codegen/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to fetch {url}: HTTP {e.code} {e.reason}") from e


@lru_cache(maxsize=8)
def resolve_commit_sha(repo: str, ref: str) -> str:
    """
    Resolve a tag/branch/ref to its full commit SHA via the GitHub API.

    If *ref* already looks like a 40-char hex SHA, returns it as-is.
    """
    if len(ref) == 40 and all(c in "0123456789abcdef" for c in ref):
        return ref

    # Use GitHub API to resolve the ref
    # Try as a tag first, then as a branch
    for ref_type in ("tags", "heads"):
        api_url = f"https://api.github.com/repos/{repo}/git/ref/{ref_type}/{ref}"
        try:
            req = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "tailscale-cli-codegen/1.0",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                obj = data.get("object", {})
                # Tags can be annotated (type=tag) or lightweight (type=commit)
                if obj.get("type") == "tag":
                    # Dereference the annotated tag to get the commit
                    tag_url = obj["url"]
                    req2 = urllib.request.Request(
                        tag_url,
                        headers={
                            "User-Agent": "tailscale-cli-codegen/1.0",
                            "Accept": "application/vnd.github.v3+json",
                        },
                    )
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        tag_data = json.loads(resp2.read())
                        return tag_data["object"]["sha"]
                return obj["sha"]
        except urllib.error.HTTPError:
            continue

    # Fallback: just use the ref as-is (maybe it's a short SHA)
    return ref


def fetch_release_tags(
    repo: str,
    *,
    stable_only: bool = True,
    min_version: tuple[int, ...] = (1, 90, 0),
) -> List[str]:
    """
    Fetch release tags from a GitHub repo.

    Parameters
    ----------
    repo : str           e.g. "tailscale/tailscale"
    stable_only : bool   If True, exclude pre-release tags (-rc, -beta, etc.)
    min_version : tuple  Only include tags >= this version.

    Returns
    -------
    List of tag strings sorted by semver ascending, e.g. ["v1.50.0", "v1.52.0", …]
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "User-Agent": "tailscale-cli-codegen/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    tags: List[str] = []
    page = 1
    per_page = 100

    while True:
        api_url = (
            f"https://api.github.com/repos/{repo}/tags"
            f"?per_page={per_page}&page={page}"
        )
        req = urllib.request.Request(api_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Failed to fetch tags from {api_url}: HTTP {e.code} {e.reason}"
            ) from e

        if not data:
            break

        for item in data:
            tag_name = item["name"]
            tags.append(tag_name)

        if len(data) < per_page:
            break
        page += 1

    # Filter to semver release tags
    version_re = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(.*)$")
    result: list[tuple[tuple[int, ...], str]] = []

    for tag in tags:
        m = version_re.match(tag)
        if not m:
            continue
        ver = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        suffix = m.group(4)

        if stable_only and suffix:
            continue
        if ver < min_version:
            continue

        result.append((ver, tag))

    # Sort ascending by version
    result.sort(key=lambda x: x[0])
    return [tag for _, tag in result]
