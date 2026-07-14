import json, os
from kestra import Kestra

finished = json.loads(os.environ['FINISHED_JSON']).get('matches', [])
qf = json.loads(os.environ['QF_JSON']).get('matches', [])
scorers = json.loads(os.environ['SCORERS_JSON']).get('scorers', [])

stats = {}

def ensure(team):
    if team not in stats:
        stats[team] = {'played': 0, 'w': 0, 'd': 0, 'l': 0, 'gf': 0, 'ga': 0,
                       'cs': 0, 'best_win': 0, 'path': []}
    return stats[team]

for m in finished:
    ft = m.get('score', {}).get('fullTime', {})
    hs, as_ = ft.get('home'), ft.get('away')
    if hs is None or as_ is None:
        continue
    home = m['homeTeam']['name']
    away = m['awayTeam']['name']
    stage = m.get('stage', '').replace('_', ' ').title()
    for team, gf, ga, opp in [(home, hs, as_, away), (away, as_, hs, home)]:
        s = ensure(team)
        s['played'] += 1
        s['gf'] += gf
        s['ga'] += ga
        if ga == 0:
            s['cs'] += 1
        if gf > ga:
            s['w'] += 1; res = 'W'
        elif gf < ga:
            s['l'] += 1; res = 'L'
        else:
            s['d'] += 1; res = 'D'
        s['best_win'] = max(s['best_win'], gf - ga)
        s['path'].append(f"{res} {gf}-{ga} v {opp} ({stage})")

team_scorers = {}
for sc in scorers:
    tname = (sc.get('team') or {}).get('name')
    pname = (sc.get('player') or {}).get('name')
    goals = sc.get('goals', 0)
    if tname and pname:
        team_scorers.setdefault(tname, []).append(f"{pname} ({goals})")

qf_teams = []
for m in qf:
    qf_teams += [m['homeTeam']['name'], m['awayTeam']['name']]

if not qf_teams:
    Kestra.outputs({'prompt': '', 'summary': 'No quarter-final fixtures found yet.', 'has_qf': 'false'})
else:
    team_lines = []
    for team in qf_teams:
        s = stats.get(team, {'played': 0, 'w': 0, 'd': 0, 'l': 0, 'gf': 0, 'ga': 0,
                             'cs': 0, 'best_win': 0, 'path': []})
        gd = s['gf'] - s['ga']
        avg_scored = s['gf'] / s['played'] if s['played'] else 0
        avg_conceded = s['ga'] / s['played'] if s['played'] else 0
        top = ", ".join(team_scorers.get(team, [])[:3]) or "no listed scorers"
        team_lines.append(
            f"{team}\n"
            f"  Record: {s['w']}W-{s['d']}D-{s['l']}L over {s['played']} matches\n"
            f"  Goals: {s['gf']} scored, {s['ga']} conceded (GD {gd:+d}, "
            f"{avg_scored:.1f} for / {avg_conceded:.1f} against per game)\n"
            f"  Clean sheets: {s['cs']} | Biggest winning margin: {s['best_win']}\n"
            f"  Top scorers: {top}\n"
            f"  Path: {'; '.join(s['path'])}"
        )
    stats_text = "\n\n".join(team_lines)

    prompt = f"""The World Cup 2026 is down to the final 8 teams. Below is every relevant statistic
from each remaining team's tournament so far.

{stats_text}
"""

    Kestra.outputs({
        'prompt': prompt,
        'prompt_escaped': json.dumps(prompt)[1:-1],
        'summary': stats_text,
        'has_qf': 'true'
    })