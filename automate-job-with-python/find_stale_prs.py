#!/usr/bin/env python3
"""Find stale open GitHub PRs and export them to CSV.

Example:
  GITHUB_TOKEN=ghp_xxx python find_stale_prs.py \
      --repo owner/name \
      --days 90 \
      --output stale_prs.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional


GITHUB_API = "https://api.github.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find open PRs with no updates older than a threshold and export to CSV."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repo in owner/name format.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Mark PR as stale if last updated more than this many days ago (default: 90).",
    )
    parser.add_argument(
        "--output",
        default="stale_prs.csv",
        help="Path for output CSV file (default: stale_prs.csv).",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN", ""),
        help="GitHub token. Defaults to GITHUB_TOKEN env var.",
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        default=2000,
        help="Maximum open PRs to scan (default: 2000).",
    )
    return parser.parse_args()


def github_request(
    path: str,
    token: str,
    method: str = "GET",
    query: Optional[Dict[str, str]] = None,
    body: Optional[Dict] = None,
) -> Dict:
    if query:
        encoded = urllib.parse.urlencode(query)
        url = f"{GITHUB_API}{path}?{encoded}"
    else:
        url = f"{GITHUB_API}{path}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "stale-pr-finder",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code} for {url}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def parse_iso8601(timestamp: str) -> dt.datetime:
    return dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def fetch_open_prs(repo: str, token: str, max_prs: int) -> List[Dict]:
    owner, name = repo.split("/", 1)
    prs: List[Dict] = []
    page = 1
    per_page = 100

    while len(prs) < max_prs:
        batch = github_request(
            f"/repos/{owner}/{name}/pulls",
            token=token,
            query={
                "state": "open",
                "sort": "updated",
                "direction": "asc",
                "per_page": str(per_page),
                "page": str(page),
            },
        )
        if not batch:
            break

        prs.extend(batch)
        if len(batch) < per_page:
            break

        page += 1

    return prs[:max_prs]


def filter_stale_prs(prs: List[Dict], cutoff: dt.datetime) -> List[Dict]:
    stale: List[Dict] = []

    for pr in prs:
        updated_at = parse_iso8601(pr["updated_at"])
        if updated_at < cutoff:
            stale.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": (pr.get("user") or {}).get("login", ""),
                    "updated_at": pr["updated_at"],
                    "created_at": pr["created_at"],
                    "html_url": pr["html_url"],
                    "draft": bool(pr.get("draft")),
                }
            )

    return stale


def write_csv(path: str, rows: List[Dict]) -> None:
    fields = [
        "number",
        "title",
        "author",
        "updated_at",
        "created_at",
        "draft",
        "html_url",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()

    if args.days <= 0:
        print("--days must be a positive integer", file=sys.stderr)
        return 2

    if "/" not in args.repo:
        print("--repo must be in owner/name format", file=sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=args.days)

    prs = fetch_open_prs(repo=args.repo, token=args.token, max_prs=args.max_prs)
    stale_prs = filter_stale_prs(prs=prs, cutoff=cutoff)
    write_csv(args.output, stale_prs)

    print(f"Scanned {len(prs)} open PR(s) in {args.repo}")
    print(f"Found {len(stale_prs)} stale PR(s) older than {args.days} days")
    print(f"Wrote CSV: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
