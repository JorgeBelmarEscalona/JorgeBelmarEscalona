"""Genera las tarjetas SVG dinámicas del perfil.

Salida (OUT_DIR): stats.svg, langs.svg, activity.svg y repo-<nombre>.svg.

Usa STATS_TOKEN si existe (PAT con scopes `repo` y `read:org`, incluye repos
privados propios y de organizaciones en lenguajes y conteos); si no, GITHUB_TOKEN, que solo ve lo público.
"""
import datetime as dt
import json
import os
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "JorgeBelmarEscalona")
TOKEN = os.environ.get("STATS_TOKEN") or os.environ["GITHUB_TOKEN"]
PRIVATE = bool(os.environ.get("STATS_TOKEN"))
OUT = os.environ.get("OUT_DIR", "dist")

# Repos a ignorar (nombres separados por coma), p. ej. proyectos en los que no participas.
EXCLUDE_REPOS = {n.strip() for n in os.environ.get("EXCLUDE_REPOS", "").split(",") if n.strip()}
EXCLUDE_LANGS = {"Jupyter Notebook", "Makefile", "CMake", "Dockerfile"}

# Descripciones propias: la mayoría de los repos no tiene descripción en GitHub.
FEATURED = {
    "bionic-reading": "Convierte libros EPUB a formato Bionic Reading para leer más rápido. Interfaz gráfica y CLI.",
    "calibre-api": "API REST con FastAPI para convertir e-books entre formatos (EPUB, PDF, MOBI, DOCX…) usando Calibre.",
    "Tsensormadera": "Monitor de escritorio que lee datos de sensores desde Google Sheets y los grafica en tiempo real.",
    "WSAPatch": "Parche para ejecutar Windows Subsystem for Android en Windows 10.",
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
HEAT = {
    "NONE": "#13212B",
    "FIRST_QUARTILE": "#1A4A42",
    "SECOND_QUARTILE": "#23765A",
    "THIRD_QUARTILE": "#35A57A",
    "FOURTH_QUARTILE": "#5FD6A8",
}
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

USER_QUERY = """
query($login: String!, $privacy: RepositoryPrivacy, $cursor: String) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions restrictedContributionsCount totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, after: $cursor, ownerAffiliations: [OWNER, ORGANIZATION_MEMBER], isFork: false, privacy: $privacy) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}"""

REPO_FIELDS = "name url stargazerCount forkCount primaryLanguage { name color }"


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]


def fetch_user():
    variables = {"login": USER, "privacy": None if PRIVATE else "PUBLIC", "cursor": None}
    repos = []
    while True:
        user = gql(USER_QUERY, variables)["user"]
        page = user["repositories"]
        repos += [r for r in page["nodes"] if r["name"] not in EXCLUDE_REPOS]
        if not page["pageInfo"]["hasNextPage"]:
            return user, repos
        variables["cursor"] = page["pageInfo"]["endCursor"]


def fetch_featured():
    aliases = "\n".join(
        f'r{i}: repository(owner: "{USER}", name: "{name}") {{ {REPO_FIELDS} }}'
        for i, name in enumerate(FEATURED)
    )
    data = gql(f"query {{ {aliases} }}", {})
    return [data[f"r{i}"] for i in range(len(FEATURED))]


# ─────────────────────────── helpers de dibujo ───────────────────────────

def svg(width, height, label, body, glow=True):
    glow_el = (
        f'<circle cx="{width}" cy="0" r="{width * .6:.0f}" fill="url(#glow)"/>' if glow else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0B1822"/><stop offset="1" stop-color="#0E2330"/></linearGradient>
  <radialGradient id="glow"><stop offset="0" stop-color="#4FC39A" stop-opacity=".13"/><stop offset="1" stop-color="#4FC39A" stop-opacity="0"/></radialGradient>
  <clipPath id="card"><rect width="{width}" height="{height}" rx="18"/></clipPath>
</defs>
<style>
  .sans {{ font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; }}
  .in   {{ opacity: 0; animation: in .7s cubic-bezier(.2,.8,.2,1) forwards; }}
  .pop  {{ opacity: 0; animation: pop .45s ease-out forwards; }}
  .grow {{ transform: scaleX(0); animation: grow 1.1s cubic-bezier(.2,.8,.2,1) .2s forwards; }}
  @keyframes in   {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes pop  {{ to {{ opacity: 1; }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
</style>
<g clip-path="url(#card)"><rect width="{width}" height="{height}" fill="url(#bg)"/>{glow_el}</g>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="17.5" fill="none" stroke="#FFFFFF" stroke-opacity=".08"/>
{body}
</svg>"""


def eyebrow(x, y, text):
    return (
        f'<text x="{x}" y="{y}" class="mono in" font-size="11" font-weight="700" '
        f'fill="#4FC39A" letter-spacing="1.4">{escape(text.upper())}</text>'
    )


def wrap(text, limit):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


# ─────────────────────────── tarjetas ───────────────────────────

def stats_card(user, repos):
    c = user["contributionsCollection"]
    metrics = [
        (c["totalCommitContributions"] + c["restrictedContributionsCount"], "commits en el año"),
        (c["totalPullRequestContributions"], "pull requests"),
        (len(languages(repos)), "lenguajes"),
        (user["repositories"]["totalCount"], "repositorios" if PRIVATE else "repos públicos"),
        (sum(r["stargazerCount"] for r in repos), "estrellas"),
        (user["followers"]["totalCount"], "seguidores"),
    ]
    body = [eyebrow(28, 42, "En números")]
    for i, (value, label) in enumerate(metrics):
        x, y = 28 + (i % 3) * 128, 96 + (i // 3) * 72
        body.append(
            f'<g class="in" style="animation-delay:{120 + i * 80}ms">'
            f'<text x="{x}" y="{y}" class="sans" font-size="28" font-weight="800" fill="#FFFFFF" letter-spacing="-.5">{value:,}</text>'
            f'<text x="{x}" y="{y + 22}" class="sans" font-size="12.5" fill="#7D8FA0">{escape(label)}</text></g>'
        )
    return svg(405, 220, "Estadísticas de GitHub", "\n".join(body))


def languages(repos):
    totals = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in EXCLUDE_LANGS:
                continue
            size, _ = totals.get(name, (0, None))
            totals[name] = (size + edge["size"], edge["node"]["color"] or "#7D8FA0")
    return totals


def langs_card(repos):
    totals = languages(repos)
    top = sorted(totals.items(), key=lambda kv: kv[1][0], reverse=True)[:6]
    grand = sum(size for _, (size, _) in top) or 1

    bar_x, bar_w = 28, 349
    body = [
        eyebrow(28, 42, "Lenguajes"),
        f'<clipPath id="bar"><rect x="{bar_x}" y="66" width="{bar_w}" height="10" rx="5"/></clipPath>',
        f'<rect x="{bar_x}" y="66" width="{bar_w}" height="10" rx="5" fill="#FFFFFF" fill-opacity=".06"/>',
        f'<g clip-path="url(#bar)"><g class="grow" style="transform-origin:{bar_x}px 0">',
    ]
    x = bar_x
    for _, (size, color) in top:
        w = bar_w * size / grand
        body.append(f'<rect x="{x:.2f}" y="66" width="{w + .6:.2f}" height="10" fill="{color}"/>')
        x += w
    body.append("</g></g>")
    for i, (name, (size, color)) in enumerate(top):
        cx, cy = 34 + (i % 2) * 176, 112 + (i // 2) * 34
        body.append(
            f'<g class="in" style="animation-delay:{350 + i * 70}ms">'
            f'<circle cx="{cx}" cy="{cy - 4.5}" r="5" fill="{color}"/>'
            f'<text x="{cx + 14}" y="{cy}" class="sans" font-size="13.5" font-weight="600" fill="#E6EDF3">{escape(name)}</text>'
            f'<text x="{cx + 150}" y="{cy}" class="mono" font-size="12" fill="#7D8FA0" text-anchor="end">{100 * size / grand:.1f}%</text></g>'
        )
    return svg(405, 220, "Lenguajes más usados", "\n".join(body))


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for n in counts:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    i = len(counts) - 1
    if counts and counts[i] == 0:  # hoy todavía sin contribuciones: no corta la racha
        i -= 1
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    return current, longest


def activity_card(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"][-32:]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    current, longest = streaks(days)

    body = [
        eyebrow(28, 42, "Actividad · último año"),
        f'<text x="28" y="98" class="sans in" font-size="44" font-weight="800" fill="#FFFFFF" letter-spacing="-1">{cal["totalContributions"]:,}</text>',
        '<text x="28" y="122" class="sans in" font-size="13" fill="#7D8FA0">contribuciones</text>',
    ]
    for i, (value, label) in enumerate([(current, "racha actual"), (longest, "racha más larga")]):
        x = 28 + i * 110
        body.append(
            f'<g class="in" style="animation-delay:{200 + i * 100}ms">'
            f'<text x="{x}" y="166" class="sans" font-size="22" font-weight="800" fill="#7FD8B4">{value}'
            f'<tspan font-size="13" font-weight="600" fill="#7D8FA0"> {"día" if value == 1 else "días"}</tspan></text>'
            f'<text x="{x}" y="186" class="sans" font-size="12" fill="#7D8FA0">{label}</text></g>'
        )

    cell, gap = 13, 3
    grid_x = 802 - len(weeks) * (cell + gap) + gap
    grid_y = 58
    last_month = None
    for wi, week in enumerate(weeks):
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month and wi < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                body.append(
                    f'<text x="{grid_x + wi * (cell + gap)}" y="{grid_y - 10}" class="sans" font-size="10.5" fill="#5F7385">{MONTHS[first.month - 1]}</text>'
                )
            last_month = first.month
        # la primera semana puede venir incompleta: se alinea por día de la semana
        for day in week["contributionDays"]:
            wd = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7  # domingo = 0
            body.append(
                f'<rect class="pop" style="animation-delay:{wi * 28}ms" x="{grid_x + wi * (cell + gap)}" '
                f'y="{grid_y + wd * (cell + gap)}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{HEAT[day["contributionLevel"]]}"><title>{day["date"]}: {day["contributionCount"]}</title></rect>'
            )
    legend_y = grid_y + 7 * (cell + gap) + 12
    lx = 802 - 5 * 14 - 40
    body.append(f'<text x="{lx - 8}" y="{legend_y + 9}" class="sans" font-size="10.5" fill="#5F7385" text-anchor="end">menos</text>')
    for i, color in enumerate(HEAT.values()):
        body.append(f'<rect x="{lx + i * 14}" y="{legend_y}" width="10" height="10" rx="2.5" fill="{color}"/>')
    body.append(f'<text x="{lx + 5 * 14 + 4}" y="{legend_y + 9}" class="sans" font-size="10.5" fill="#5F7385">más</text>')
    return svg(830, 215, "Actividad de contribuciones", "\n".join(body))


def repo_card(repo, description):
    lang = repo["primaryLanguage"] or {"name": "—", "color": "#7D8FA0"}
    body = [
        '<g class="in" fill="none" stroke="#7D8FA0" stroke-width="1.5" stroke-linejoin="round">'
        '<path d="M30 30 h9 a3 3 0 0 1 3 3 v14 a2.5 2.5 0 0 0 -2.5 -2.5 H30 z"/>'
        '<path d="M30 30 v14.5 M42 33 v14"/></g>',
        f'<text x="54" y="45" class="sans in" font-size="17" font-weight="700" fill="#FFFFFF">{escape(repo["name"])}</text>',
        '<g class="in" style="animation-delay:.1s" fill="#7D8FA0"><path d="M377 33 l4 4 -4 4" stroke="#7D8FA0" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>',
    ]
    for i, line in enumerate(wrap(description, 50)[:3]):
        body.append(
            f'<text x="28" y="{80 + i * 21}" class="sans in" style="animation-delay:.1s" font-size="13.5" fill="#B5C6D2">{escape(line)}</text>'
        )
    star = (
        "M0 -6.5 L1.9 -2.1 6.6 -1.7 3 1.4 4.1 6 0 3.6 -4.1 6 -3 1.4 -6.6 -1.7 -1.9 -2.1 z"
    )
    body.append(
        '<g class="in" style="animation-delay:.2s">'
        f'<circle cx="34" cy="150" r="5.5" fill="{lang["color"]}"/>'
        f'<text x="46" y="155" class="sans" font-size="13" fill="#B5C6D2">{escape(lang["name"])}</text>'
        f'<path transform="translate(148 150)" d="{star}" fill="none" stroke="#7D8FA0" stroke-width="1.3" stroke-linejoin="round"/>'
        f'<text x="162" y="155" class="sans" font-size="13" fill="#B5C6D2">{repo["stargazerCount"]}</text>'
        "</g>"
    )
    return svg(405, 180, repo["name"], "\n".join(body), glow=False)


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    os.makedirs(OUT, exist_ok=True)
    user, repos = fetch_user()
    write("stats.svg", stats_card(user, repos))
    write("langs.svg", langs_card(repos))
    write("activity.svg", activity_card(user))
    for repo in fetch_featured():
        write(f"repo-{repo['name']}.svg", repo_card(repo, FEATURED[repo["name"]]))
    print(f"OK: {len(repos)} repos ({'incluye privados' if PRIVATE else 'solo públicos'})")


if __name__ == "__main__":
    main()
