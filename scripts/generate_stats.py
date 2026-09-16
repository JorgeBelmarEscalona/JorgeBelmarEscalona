"""Actualiza la sección de actividad del perfil.

- Genera en OUT_DIR: activity-{light,dark}.svg y langs-{light,dark}.svg
- Reescribe el bloque <!-- stats:start --> … <!-- stats:end --> del README.

Usa STATS_TOKEN si existe (PAT con scopes `repo` y `read:org`: incluye repos
privados propios y de organizaciones); si no, GITHUB_TOKEN, que solo ve lo público.
EXCLUDE_REPOS: nombres de repos a ignorar, separados por coma.
"""
import datetime as dt
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "JorgeBelmarEscalona")
TOKEN = os.environ.get("STATS_TOKEN") or os.environ["GITHUB_TOKEN"]
PRIVATE = bool(os.environ.get("STATS_TOKEN"))
OUT = os.environ.get("OUT_DIR", "dist")
README = os.environ.get("README", "README.md")
RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/output"

EXCLUDE_REPOS = {n.strip() for n in os.environ.get("EXCLUDE_REPOS", "").split(",") if n.strip()}
EXCLUDE_LANGS = {"Jupyter Notebook", "Makefile", "CMake", "Dockerfile", "Hack", "Mako"}
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

THEMES = {
    "light": {
        "muted": "#656D76", "bg": "#FFFFFF", "accent": "#2F7A5F",
        "levels": ["#EBEEF1", "#C6E6D7", "#8CCBAE", "#4E9E7D", "#2F7A5F"],
    },
    "dark": {
        "muted": "#8B949E", "bg": "#0D1117", "accent": "#5BB08F",
        "levels": ["#161B22", "#1B3B30", "#24604A", "#3A8F6C", "#5BB08F"],
    },
}
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!, $privacy: RepositoryPrivacy, $cursor: String) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, after: $cursor, ownerAffiliations: [OWNER, ORGANIZATION_MEMBER], isFork: false, privacy: $privacy) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}"""


def gql(variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]["user"]


def fetch():
    variables = {"login": USER, "privacy": None if PRIVATE else "PUBLIC", "cursor": None}
    repos = []
    while True:
        user = gql(variables)
        page = user["repositories"]
        repos += [r for r in page["nodes"] if r["name"] not in EXCLUDE_REPOS]
        if not page["pageInfo"]["hasNextPage"]:
            return user, repos
        variables["cursor"] = page["pageInfo"]["endCursor"]


def languages(repos):
    totals = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in EXCLUDE_LANGS:
                continue
            size, _ = totals.get(name, (0, None))
            totals[name] = (size + edge["size"], edge["node"]["color"] or "#8B949E")
    top = sorted(totals.items(), key=lambda kv: kv[1][0], reverse=True)[:6]
    grand = sum(size for _, (size, _) in top) or 1
    return [(name, color, 100 * size / grand) for name, (size, color) in top]


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for n in counts:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current, i = 0, len(counts) - 1
    if counts and counts[i] == 0:  # hoy todavía sin contribuciones: no corta la racha
        i -= 1
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    return current, longest


# ─────────────────────────── SVG ───────────────────────────

def activity_svg(weeks, c):
    cols = len(weeks)
    step = 830 / cols
    cell = step - 3.2
    top = 22
    height = top + 7 * step
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="830" height="{height:.0f}" viewBox="0 0 830 {height:.0f}" role="img" aria-label="Calendario de contribuciones">',
        "<style>",
        "  .c { opacity: 0; animation: in .5s ease-out forwards; }",
        "  @keyframes in { from { opacity: 0; } to { opacity: 1; } }",
        "  .today { transform-box: fill-box; transform-origin: center; animation: ping 2.8s ease-out 2s infinite; opacity: 0; }",
        "  @keyframes ping { 0% { opacity: .7; transform: scale(1); } 70%, 100% { opacity: 0; transform: scale(2.4); } }",
        "</style>",
    ]
    last_month = None
    for wi, week in enumerate(weeks):
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month:
            if last_month is not None and wi < cols - 2:
                parts.append(
                    f'<text x="{wi * step:.1f}" y="12" font-family="{SANS}" font-size="12" fill="{c["muted"]}">{MONTHS[first.month - 1]}</text>'
                )
            last_month = first.month
        for day in week["contributionDays"]:
            wd = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7  # domingo = 0
            parts.append(
                f'<rect class="c" style="animation-delay:{wi * 22}ms" x="{wi * step:.1f}" y="{top + wd * step:.1f}" '
                f'width="{cell:.1f}" height="{cell:.1f}" rx="2.5" fill="{c["levels"][LEVEL[day["contributionLevel"]]]}">'
                f'<title>{day["date"]}: {day["contributionCount"]}</title></rect>'
            )
    last_day = weeks[-1]["contributionDays"][-1]
    wd = (dt.date.fromisoformat(last_day["date"]).weekday() + 1) % 7
    parts.append(
        f'<rect class="today" x="{(cols - 1) * step:.1f}" y="{top + wd * step:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" '
        f'fill="none" stroke="{c["accent"]}" stroke-width="1.5"/>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def langs_svg(langs, c):
    gap, x = 4, 0.0
    usable = 830 - gap * (len(langs) - 1)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="830" height="10" viewBox="0 0 830 10" role="img" aria-label="Lenguajes">',
        "<style>",
        "  .s { transform: scaleX(0); animation: grow .9s cubic-bezier(.2,.7,.2,1) forwards; }",
        "  @keyframes grow { to { transform: scaleX(1); } }",
        "</style>",
    ]
    for i, (_, color, pct) in enumerate(langs):
        w = max(usable * pct / 100, 6)
        parts.append(
            f'<rect class="s" style="transform-origin:{x:.1f}px 0;animation-delay:{i * 120}ms" x="{x:.1f}" y="0" width="{w:.1f}" height="10" rx="5" fill="{color}"/>'
        )
        x += w + gap
    parts.append("</svg>")
    return "\n".join(parts)


# ─────────────────────────── README ───────────────────────────

def picture(name, alt, width="100%"):
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}-dark.svg">\n'
        f'  <img src="{RAW}/{name}-light.svg" alt="{alt}" width="{width}">\n'
        "</picture>"
    )


def dias(n):
    return f"{n} día" if n == 1 else f"{n} días"


def readme_block(user, langs, current, longest):
    c = user["contributionsCollection"]
    cal = c["contributionCalendar"]
    lang_line = " · ".join(f"{name} {pct:.0f}%" for name, _, pct in langs if pct >= 1)
    return f"""<!-- stats:start -->
{picture("activity", "Calendario de contribuciones")}

**{cal["totalContributions"]:,}** contribuciones en el último año · racha más larga de **{dias(longest)}** · {lang_line}
<!-- stats:end -->"""


def main():
    user, repos = fetch()
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    current, longest = streaks(days)
    langs = languages(repos)

    os.makedirs(OUT, exist_ok=True)
    for theme, colors in THEMES.items():
        with open(os.path.join(OUT, f"activity-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(activity_svg(cal["weeks"][-52:], colors))
        with open(os.path.join(OUT, f"langs-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(langs_svg(langs, colors))

    with open(README, encoding="utf-8") as f:
        readme = f.read()
    updated = re.sub(
        r"<!-- stats:start -->.*?<!-- stats:end -->",
        lambda _: readme_block(user, langs, current, longest),
        readme,
        flags=re.S,
    )
    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"OK: {len(repos)} repos ({'incluye privados' if PRIVATE else 'solo públicos'})")


if __name__ == "__main__":
    main()
