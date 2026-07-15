# Fetch one Tour de France 2026 stage from ProCyclingStats.
# PCS sits behind Cloudflare, which fingerprints the TLS handshake and 403s
# plain clients. curl_cffi impersonates a real Chrome handshake to get through,
# then we hand the HTML to the procyclingstats parser instead of letting it
# fetch itself.

import json
import os
import sys

from curl_cffi import requests as cffi
from procyclingstats import Stage

BASE = "https://www.procyclingstats.com"


def parse_time_to_seconds(t):
    if not t:
        return None
    parts = [int(p) for p in t.split(":")]
    secs = 0
    for p in parts:
        secs = secs * 60 + p
    return secs


def fetch_stage(stage_number: int):
    """Return the stage's data, or None if results aren't published yet."""
    path = f"race/tour-de-france/2026/stage-{stage_number}"
    # impersonate a real Chrome TLS fingerprint; transient blocks are retried
    # by the Kestra task's retry block.
    resp = cffi.get(f"{BASE}/{path}", impersonate="chrome", timeout=30)
    resp.raise_for_status()

    stage = Stage(path, html=resp.text, update_html=False)

    results = stage.results()
    gc = stage.gc()
    if not results or not gc:
        # page exists but the stage hasn't finished / been posted; caller skips
        return None

    leader_secs = parse_time_to_seconds(gc[0]["time"])

    data = {
        "stage": stage_number,
        "date": stage.date(),
        "distance_km": stage.distance(),
        "winner": {
            "name": results[0]["rider_name"],
            "team": results[0]["team_name"],
            "time": results[0]["time"],
        },
        "stage_top10": [
            {
                "rank": r["rank"],
                "name": r["rider_name"],
                "team": r["team_name"],
                "breakaway_kms": r.get("breakaway_kms"),
            }
            for r in results[:10]
        ],
        # top 30 is enough for GC trends and team-strength stats
        "gc_top30": [
            {
                "rank": r["rank"],
                "prev_rank": r.get("prev_rank"),
                "name": r["rider_name"],
                "team": r["team_name"],
                "gap_seconds": parse_time_to_seconds(r["time"]) - leader_secs,
            }
            for r in gc[:30]
        ],
        # longest days in the breakaway, the work TV forgets by the finish
        "breakaway_kms": sorted(
            [
                {"name": r["rider_name"], "kms": r["breakaway_kms"]}
                for r in results
                if r.get("breakaway_kms")
            ],
            key=lambda x: -x["kms"],
        )[:5],
    }
    return data


if __name__ == "__main__":
    stage_number = int(sys.argv[1] if len(sys.argv) > 1 else os.environ["STAGE_NUMBER"])
    data = fetch_stage(stage_number)
    if data is None:
        print(f"stage {stage_number}: no results published yet")
        sys.exit(0)
    print(json.dumps(data, indent=2))

    # inside Kestra, expose the stage data as an output
    try:
        from kestra import Kestra

        Kestra.outputs({"stage_data": data})
    except ImportError:
        pass
