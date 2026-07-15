# Cross-stage analysis for the Tour de France briefing.
# Reads the accumulated stage data (a dict keyed by stage number),
# renders the GC gap-trend chart, and writes a text briefing.

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# categorical palette, fixed order (validated for CVD separation)
PALETTE = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948"]

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"


def load_stages(path):
    with open(path) as f:
        raw = json.load(f)
    # keys arrive as strings from JSON
    return {int(k): v for k, v in raw.items()}


def gap_series(stages, rider):
    """Gap to leader (minutes) per stage for one rider, None if outside top 30."""
    out = []
    for n in sorted(stages):
        row = next((r for r in stages[n]["gc_top30"] if r["name"] == rider), None)
        out.append(row["gap_seconds"] / 60 if row else None)
    return out


def last_name(rider_name):
    # PCS returns "Surname(s) Firstname"; the first name is the last token, so
    # the surname is everything before it (keeps "del Toro", "van der Poel").
    parts = rider_name.split(" ")
    return " ".join(parts[:-1]) if len(parts) > 1 else rider_name


def make_chart(stages, out_path):
    latest = stages[max(stages)]
    # follow the riders currently in the GC top 6
    riders = [r["name"] for r in latest["gc_top30"][:6]]
    stage_numbers = sorted(stages)

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ends = []
    for i, rider in enumerate(riders):
        series = gap_series(stages, rider)
        color = PALETTE[i % len(PALETTE)]
        ax.plot(stage_numbers, series, color=color, linewidth=2, label=rider)
        if series[-1] is not None:
            ends.append((series[-1], last_name(rider), color))

    # direct labels at line ends, nudged apart when riders finish on the same time
    ends.sort()
    y_span = max(e[0] for e in ends) - min(e[0] for e in ends) or 1
    min_gap = y_span * 0.045
    placed = []
    for y, surname, color in ends:
        y_label = y
        if placed and y_label - placed[-1] < min_gap:
            y_label = placed[-1] + min_gap
        placed.append(y_label)
        ax.annotate(
            f" {surname}",
            (stage_numbers[-1], y_label),
            color=color,
            fontsize=9,
            fontweight="bold",
            va="center",
        )

    ax.invert_yaxis()  # leader at the top, bigger gap sinks
    ax.set_xticks(stage_numbers)
    ax.set_xlabel("Stage", color=TEXT_SECONDARY)
    ax.set_ylabel("Gap to race leader (minutes)", color=TEXT_SECONDARY)
    ax.set_title(
        f"Tour de France 2026 · GC gap to leader after stage {max(stages)}",
        color=TEXT_PRIMARY,
        fontsize=13,
        loc="left",
    )
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#d0cfc8")
    ax.tick_params(colors=TEXT_SECONDARY)
    ax.legend(frameon=False, fontsize=9, labelcolor=TEXT_PRIMARY)
    ax.margins(x=0.12)  # room for the direct labels

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


def fmt_gap(seconds):
    if seconds == 0:
        return "leader"
    m, s = divmod(seconds, 60)
    return f"+{m}:{s:02d}"


def make_briefing(stages):
    latest = stages[max(stages)]
    lines = []
    lines.append(f"*TDF 2026 briefing, after stage {latest['stage']} ({latest['date']})*")
    lines.append(
        f"Stage winner: {latest['winner']['name']} ({latest['winner']['team']}), "
        f"{latest['distance_km']} km"
    )

    lines.append("")
    lines.append("*GC top 5*")
    for r in latest["gc_top30"][:5]:
        move = ""
        if r.get("prev_rank"):
            delta = r["prev_rank"] - r["rank"]
            if delta > 0:
                move = f" (up {delta})"
            elif delta < 0:
                move = f" (down {-delta})"
        lines.append(f"{r['rank']}. {r['name']}, {fmt_gap(r['gap_seconds'])}{move}")

    # biggest mover inside the top 30 today
    movers = [r for r in latest["gc_top30"] if r.get("prev_rank")]
    if movers:
        big = max(movers, key=lambda r: r["prev_rank"] - r["rank"])
        if big["prev_rank"] - big["rank"] > 0:
            lines.append("")
            lines.append(
                f"*Biggest mover:* {big['name']}, "
                f"{big['prev_rank']} -> {big['rank']} on GC"
            )

    # team strength: riders per team still in the GC top 30
    teams = {}
    for r in latest["gc_top30"]:
        teams[r["team"]] = teams.get(r["team"], 0) + 1
    strongest = sorted(teams.items(), key=lambda kv: -kv[1])[:3]
    lines.append("")
    lines.append("*Strongest teams (riders in GC top 30)*")
    for team, count in strongest:
        lines.append(f"{team}: {count}")

    if latest.get("breakaway_kms"):
        lines.append("")
        lines.append("*Longest in the breakaway today*")
        for b in latest["breakaway_kms"][:3]:
            lines.append(f"{b['name']}: {b['kms']} km off the front")

    return "\n".join(lines)


if __name__ == "__main__":
    stages_file = sys.argv[1] if len(sys.argv) > 1 else "stages.json"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    stages = load_stages(stages_file)

    chart_path = os.path.join(out_dir, "gc_trend.png")
    make_chart(stages, chart_path)

    briefing = make_briefing(stages)
    briefing_path = os.path.join(out_dir, "briefing.txt")
    with open(briefing_path, "w") as f:
        f.write(briefing)
    print(briefing)

    try:
        from kestra import Kestra

        Kestra.outputs({"briefing": briefing})
    except ImportError:
        pass
