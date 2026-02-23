#!/usr/bin/env python3
"""Prioritize open GitHub PRs and export top results to CSV.

Example:
  GITHUB_TOKEN=ghp_xxx python prioritize_kestra_prs.py \
      --repo kestra-io/kestra \
      --output top_kestra_prs.csv \
      --top 10
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
from typing import Dict, List, Tuple


GITHUB_API = "https://api.github.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch open GitHub PRs, prioritize them, and write a CSV."
    )
    parser.add_argument(
        "--repo",
        default="kestra-io/kestra",
        help="GitHub repo in owner/name format (default: kestra-io/kestra)",
    )
    parser.add_argument(
        "--output",
        default="top_prs.csv",
        help="Path for output CSV file (default: top_prs.csv)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of prioritized PRs to include in CSV (default: 10)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN", ""),
        help="GitHub token. Defaults to GITHUB_TOKEN env var.",
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        default=250,
        help="Max number of open PRs to analyze before ranking (default: 250)",
    )
    return parser.parse_args()


def github_request(path: str, token: str, query: Dict[str, str] | None = None) -> Dict:
    if query:
        encoded = urllib.parse.urlencode(query)
        url = f"{GITHUB_API}{path}?{encoded}"
    else:
        url = f"{GITHUB_API}{path}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "kestra-pr-prioritizer",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url=url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code} for {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def fetch_open_prs(repo: str, token: str, max_prs: int) -> List[Dict]:
    owner, name = repo.split("/", 1)
    prs: List[Dict] = []
    page = 1
    per_page = 100

    while len(prs) < max_prs:
        batch = github_request(
            f"/repos/{owner}/{name}/pulls",
            token=token,
            query={"state": "open", "sort": "updated", "direction": "desc", "per_page": str(per_page), "page": str(page)},
        )
        if not batch:
            break
        prs.extend(batch)
        if len(batch) < per_page:
            break
        page += 1

    return prs[:max_prs]


def fetch_pr_details(repo: str, token: str, number: int) -> Dict:
    owner, name = repo.split("/", 1)
    return github_request(f"/repos/{owner}/{name}/pulls/{number}", token=token)


def parse_iso8601(timestamp: str) -> dt.datetime:
    # GitHub uses UTC timestamps like "2026-02-20T18:42:23Z"
    return dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def score_pr(pr: Dict, now: dt.datetime) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    draft = bool(pr.get("draft"))
    created_at = parse_iso8601(pr["created_at"])
    updated_at = parse_iso8601(pr["updated_at"])
    age_days = (now - created_at).days
    stale_days = (now - updated_at).days

    mergeable_state = pr.get("mergeable_state") or "unknown"
    requested_reviewers = len(pr.get("requested_reviewers") or [])
    requested_teams = len(pr.get("requested_teams") or [])
    comments = int(pr.get("comments") or 0)
    review_comments = int(pr.get("review_comments") or 0)
    changed_files = int(pr.get("changed_files") or 0)
    additions = int(pr.get("additions") or 0)
    deletions = int(pr.get("deletions") or 0)
    total_discussion = comments + review_comments
    labels = [l.get("name", "").lower() for l in pr.get("labels", [])]

    if draft:
        score -= 30
        reasons.append("draft")
    else:
        score += 18
        reasons.append("ready-for-review")

    if mergeable_state in {"blocked", "dirty"}:
        score += 22
        reasons.append(f"mergeable_state={mergeable_state}")
    elif mergeable_state == "behind":
        score += 15
        reasons.append("needs-rebase")
    elif mergeable_state == "clean":
        score += 8
    elif mergeable_state == "unstable":
        score += 10

    if requested_reviewers > 0 or requested_teams > 0:
        score += 20 + 5 * requested_teams
        reasons.append("review-requested")

    if stale_days <= 1:
        score += 20
        reasons.append("recent-activity")
    elif stale_days <= 3:
        score += 14
    elif stale_days <= 7:
        score += 8
    elif stale_days > 30:
        score -= 8
        reasons.append("stale")

    if age_days <= 2:
        score += 10
    elif age_days <= 7:
        score += 8
    elif age_days <= 21:
        score += 4
    elif age_days > 120:
        score -= 10
        reasons.append("very-old")

    if total_discussion > 0:
        discussion_bonus = min(16, total_discussion * 1.5)
        score += discussion_bonus
        reasons.append("active-discussion")

    critical_keywords = ("security", "critical", "urgent", "regression", "bug", "hotfix", "release")
    matched_labels = [label for label in labels if any(k in label for k in critical_keywords)]
    if matched_labels:
        score += 6 + min(12, len(matched_labels) * 4)
        reasons.append(f"labels={';'.join(matched_labels)}")

    churn = additions + deletions
    if changed_files > 35 or churn > 4000:
        score -= 5
        reasons.append("very-large-change")
    elif changed_files <= 8 and churn <= 500 and not draft:
        score += 4
        reasons.append("small-reviewable-change")

    return round(score, 2), reasons


def prioritize_prs(repo: str, token: str, max_prs: int) -> List[Dict]:
    now = dt.datetime.now(dt.timezone.utc)
    base_prs = fetch_open_prs(repo=repo, token=token, max_prs=max_prs)

    scored: List[Dict] = []
    for pr in base_prs:
        details = fetch_pr_details(repo=repo, token=token, number=pr["number"])
        score, reasons = score_pr(details, now)

        scored.append(
            {
                "number": details["number"],
                "title": details["title"],
                "url": details["html_url"],
                "author": details["user"]["login"],
                "created_at": details["created_at"],
                "updated_at": details["updated_at"],
                "draft": details.get("draft", False),
                "mergeable_state": details.get("mergeable_state", "unknown"),
                "requested_reviewers": len(details.get("requested_reviewers") or []),
                "requested_teams": len(details.get("requested_teams") or []),
                "comments": int(details.get("comments") or 0),
                "review_comments": int(details.get("review_comments") or 0),
                "changed_files": int(details.get("changed_files") or 0),
                "additions": int(details.get("additions") or 0),
                "deletions": int(details.get("deletions") or 0),
                "labels": ";".join(l.get("name", "") for l in details.get("labels", [])),
                "priority_score": score,
                "priority_reasons": ";".join(reasons),
            }
        )

    scored.sort(key=lambda item: (item["priority_score"], item["updated_at"]), reverse=True)
    return scored


def write_csv(path: str, rows: List[Dict], top_n: int) -> None:
    selected = rows[:top_n]
    fieldnames = [
        "rank",
        "number",
        "title",
        "url",
        "author",
        "created_at",
        "updated_at",
        "draft",
        "mergeable_state",
        "requested_reviewers",
        "requested_teams",
        "comments",
        "review_comments",
        "changed_files",
        "additions",
        "deletions",
        "labels",
        "priority_score",
        "priority_reasons",
    ]

    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(selected, start=1):
            out = dict(row)
            out["rank"] = i
            writer.writerow(out)


def main() -> int:
    args = parse_args()

    if "/" not in args.repo:
        print("Error: --repo must be in owner/name format.", file=sys.stderr)
        return 2

    if args.top <= 0:
        print("Error: --top must be greater than 0.", file=sys.stderr)
        return 2

    if args.max_prs <= 0:
        print("Error: --max-prs must be greater than 0.", file=sys.stderr)
        return 2

    if not args.token:
        print(
            "Error: GitHub token is required to avoid strict rate limits. "
            "Set GITHUB_TOKEN or pass --token.",
            file=sys.stderr,
        )
        return 2

    try:
        prioritized = prioritize_prs(repo=args.repo, token=args.token, max_prs=args.max_prs)
        if not prioritized:
            print("No open PRs found.")
            return 0
        write_csv(args.output, prioritized, args.top)
    except RuntimeError as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote top {min(args.top, len(prioritized))} prioritized PRs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
