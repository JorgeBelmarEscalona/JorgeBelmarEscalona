"""Genera las tarjetas SVG animadas del perfil (estadísticas y lenguajes).

Usa STATS_TOKEN si existe (PAT con scope `repo`, incluye repos privados);
si no, GITHUB_TOKEN, que solo ve repos públicos.
"""
import json
import os
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "JorgeBelmarEscalona")
TOKEN = os.environ.get("STATS_TOKEN") or os.environ["GITHUB_TOKEN"]
PRIVATE = bool(os.environ.get("STATS_TOKEN"))
OUT = os.environ.get("OUT_DIR", "dist")

BG, BORDER, ACCENT, TEXT, MUTED = "#0D1B26", "#1F5A6B", "#4FC39A", "#AFC3D2", "#5F6B78"
EXCLUDE = {"Jupyter Notebook", "Makefile", "CMake", "Dockerfile"}

QUERY = """
query($login: String!, $privacy: RepositoryPrivacy, $cursor: String) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions restrictedContributionsCount
      totalPullRequestContributions totalIssueContributions
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false, privacy: $privacy) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
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
    repos, user = [], None
    while True:
        user = gql(variables)
        page = user["repositories"]
        repos += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return user, repos
        variables["cursor"] = page["pageInfo"]["endCursor"]


def card(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<style>
  text {{ font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; }}
  .title {{ font-size: 18px; font-weight: 700; fill: {ACCENT}; }}
  .label {{ font-size: 14px; fill: {TEXT}; }}
  .value {{ font-size: 14px; font-weight: 700; fill: #FFFFFF; }}
  .small {{ font-size: 12px; fill: {TEXT}; }}
  .fade {{ opacity: 0; animation: fade .6s ease-out forwards; }}
  .grow {{ transform: scaleX(0); animation: grow 1s cubic-bezier(.2,.8,.2,1) forwards; }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateX(-8px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
</style>
<rect x="0.5" y="0.5" rx="10" width="{width - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}"/>
<text x="25" y="36" class="title fade">{escape(title)}</text>
{body}
</svg>"""


def stats_svg(user, repos):
    c = user["contributionsCollection"]
    rows = [
        ("⭐", "Estrellas", sum(r["stargazerCount"] for r in repos)),
        ("📝", "Commits (último año)", c["totalCommitContributions"] + c["restrictedContributionsCount"]),
        ("🔀", "Pull requests", c["totalPullRequestContributions"]),
        ("🐞", "Issues", c["totalIssueContributions"]),
        ("📦", "Repositorios", user["repositories"]["totalCount"]),
        ("🟩", "Contribuciones (último año)", c["contributionCalendar"]["totalContributions"]),
    ]
    body = []
    for i, (icon, label, value) in enumerate(rows):
        y = 72 + i * 26
        body.append(
            f'<g class="fade" style="animation-delay:{150 + i * 120}ms">'
            f'<text x="25" y="{y}" class="label">{icon}  {label}:</text>'
            f'<text x="330" y="{y}" class="value" text-anchor="end">{value:,}</text></g>'
        )
    return card(360, 230, "Estadísticas de GitHub", "\n".join(body))


def langs_svg(repos):
    totals = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in EXCLUDE:
                continue
            color = edge["node"]["color"] or MUTED
            size, _ = totals.get(name, (0, color))
            totals[name] = (size + edge["size"], color)
    top = sorted(totals.items(), key=lambda kv: kv[1][0], reverse=True)[:8]
    grand = sum(size for _, (size, _) in top) or 1

    width, bar_w = 360, 310
    body, x = [], 25
    body.append(f'<clipPath id="bar"><rect x="25" y="52" width="{bar_w}" height="10" rx="5"/></clipPath>')
    body.append('<g clip-path="url(#bar)">')
    for name, (size, color) in top:
        w = bar_w * size / grand
        body.append(
            f'<rect class="grow" style="transform-origin:25px 0" x="{x:.2f}" y="52" width="{w + 0.5:.2f}" height="10" fill="{color}"/>'
        )
        x += w
    body.append("</g>")
    for i, (name, (size, color)) in enumerate(top):
        col, row = i % 2, i // 2
        cx, cy = 30 + col * 160, 92 + row * 26
        body.append(
            f'<g class="fade" style="animation-delay:{300 + i * 90}ms">'
            f'<circle cx="{cx}" cy="{cy - 4}" r="5" fill="{color}"/>'
            f'<text x="{cx + 12}" y="{cy}" class="small">{escape(name)} <tspan fill="{MUTED}">{100 * size / grand:.1f}%</tspan></text></g>'
        )
    return card(width, 230, "Lenguajes más usados", "\n".join(body))


def main():
    user, repos = fetch()
    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/stats.svg", "w", encoding="utf-8") as f:
        f.write(stats_svg(user, repos))
    with open(f"{OUT}/langs.svg", "w", encoding="utf-8") as f:
        f.write(langs_svg(repos))
    print(f"OK: {len(repos)} repos ({'incluye privados' if PRIVATE else 'solo públicos'})")


if __name__ == "__main__":
    main()
