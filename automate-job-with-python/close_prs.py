#!/usr/bin/env python3
"""Close GitHub pull requests from a provided list of PR numbers.

Examples:
  GITHUB_TOKEN=ghp_xxx python close_prs.py \
      --repo owner/name \
      --numbers 10,11,12

  GITHUB_TOKEN=ghp_xxx python close_prs.py \
      --repo owner/name \
      --input-file stale_prs.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Set


GITHUB_API = "https://api.github.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Close pull requests by number for a GitHub repository."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repo in owner/name format.",
    )
    parser.add_argument(
        "--numbers",
        default="",
        help="Comma-separated PR numbers (for example: 10,11,12).",
    )
    parser.add_argument(
        "--input-file",
        default="",
        help="Path to a file containing PR numbers (one per line or CSV with a 'number' column).",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN", ""),
        help="GitHub token. Defaults to GITHUB_TOKEN env var.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print which PRs would be closed without making API changes.",
    )
    return parser.parse_args()


def github_patch(path: str, token: str, body: Dict) -> Dict:
    url = f"{GITHUB_API}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "stale-pr-closer",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url=url, headers=headers, data=data, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code} for {url}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def parse_numbers_arg(raw: str) -> List[int]:
    result: List[int] = []
    stripped = raw.strip()
    if not stripped:
        return result

    # Supports: --numbers "[13768, 13769]"
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON array for --numbers: {stripped!r}") from exc

        if not isinstance(parsed, list):
            raise ValueError("--numbers JSON value must be an array of integers")

        for item in parsed:
            if not isinstance(item, int) or item <= 0:
                raise ValueError(f"Invalid PR number in --numbers array: {item!r}")
            result.append(item)
        return result

    # Backward compatible: --numbers "10,11,12"
    for part in stripped.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(f"Invalid PR number in --numbers: {part!r}")
        result.append(int(part))
    return result


def parse_numbers_from_file(path: str) -> List[int]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)

        if "," in sample or "number" in sample.lower():
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "number" not in {name.strip().lower() for name in reader.fieldnames}:
                raise ValueError("CSV input must include a 'number' column")

            numbers: List[int] = []
            for row in reader:
                value = row.get("number")
                if value is None:
                    value = row.get("Number")
                if value is None:
                    continue
                value = value.strip()
                if not value:
                    continue
                if not value.isdigit():
                    raise ValueError(f"Invalid PR number in CSV: {value!r}")
                numbers.append(int(value))
            return numbers

        numbers = []
        for line in handle:
            value = line.strip()
            if not value:
                continue
            if not value.isdigit():
                raise ValueError(f"Invalid PR number in file: {value!r}")
            numbers.append(int(value))
        return numbers


def unique_sorted(numbers: List[int]) -> List[int]:
    seen: Set[int] = set()
    out: List[int] = []
    for num in numbers:
        if num in seen:
            continue
        seen.add(num)
        out.append(num)
    return sorted(out)


def close_pr(repo: str, token: str, number: int) -> Dict:
    owner, name = repo.split("/", 1)
    return github_patch(f"/repos/{owner}/{name}/pulls/{number}", token=token, body={"state": "closed"})


def main() -> int:
    args = parse_args()

    if "/" not in args.repo:
        print("--repo must be in owner/name format", file=sys.stderr)
        return 2

    numbers: List[int] = []

    try:
        numbers.extend(parse_numbers_arg(args.numbers))
        if args.input_file:
            numbers.extend(parse_numbers_from_file(args.input_file))
    except (OSError, ValueError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    numbers = unique_sorted(numbers)

    if not numbers:
        print("No PR numbers provided. Use --numbers and/or --input-file.", file=sys.stderr)
        return 2

    print(f"Target repo: {args.repo}")
    print(f"PRs to close: {', '.join(str(n) for n in numbers)}")

    if args.dry_run:
        print("Dry run enabled. No PRs were modified.")
        return 0

    if not args.token:
        print("No token provided. Set --token or GITHUB_TOKEN.", file=sys.stderr)
        return 2

    success = 0
    failures = 0

    for number in numbers:
        try:
            response = close_pr(repo=args.repo, token=args.token, number=number)
            state = response.get("state", "unknown")
            print(f"PR #{number}: state={state}")
            if state == "closed":
                success += 1
            else:
                failures += 1
        except RuntimeError as exc:
            failures += 1
            print(f"PR #{number}: failed ({exc})", file=sys.stderr)

    print(f"Completed. Success={success}, Failed={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
