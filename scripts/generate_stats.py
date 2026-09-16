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

def svg(width, height, label, body, glow=True, sweep_delay=0.0, beam=True):
    glow_el = (
        f'<circle cx="{width}" cy="0" r="{width * .6:.0f}" fill="url(#glow)">'
        f'<animate attributeName="r" values="{width * .6:.0f};{width * .72:.0f};{width * .6:.0f}" dur="9s" repeatCount="indefinite"/></circle>'
        if glow else ""
    )
    beam_el = (
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="17" fill="none" stroke="#6FE3B8" '
        f'stroke-width="1.4" pathLength="1000" stroke-dasharray="60 940" stroke-linecap="round" opacity=".7">'
        f'<animate attributeName="stroke-dashoffset" values="0;-1000" dur="12s" begin="-{sweep_delay * 2:.1f}s" repeatCount="indefinite"/></rect>'
        if beam else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0A1720"/><stop offset="1" stop-color="#0E2330"/></linearGradient>
  <radialGradient id="glow"><stop offset="0" stop-color="#4FC39A" stop-opacity=".15"/><stop offset="1" stop-color="#4FC39A" stop-opacity="0"/></radialGradient>
  <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".07"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".55"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="card"><rect width="{width}" height="{height}" rx="18"/></clipPath>
</defs>
<style>
  .sans {{ font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; font-variant-numeric: tabular-nums; }}
  .in   {{ opacity: 0; animation: in .7s cubic-bezier(.2,.8,.2,1) forwards; }}
  .pop  {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: pop .5s cubic-bezier(.3,1.6,.5,1) forwards; }}
  .grow {{ transform: scaleX(0); animation: grow 1.3s cubic-bezier(.2,.8,.2,1) .2s forwards; }}
  .pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 2s ease-out infinite; }}
  .nudge {{ animation: nudge 2.4s ease-in-out infinite; }}
  .wave {{ opacity: 0; animation: wave 5s ease-in-out infinite; }}
  .breathe {{ transform-box: fill-box; transform-origin: center; animation: breathe 3s ease-in-out infinite; }}
  .flame {{ transform-box: fill-box; transform-origin: bottom center; animation: flame 1.2s ease-in-out infinite; }}
  @keyframes in   {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes pop  {{ from {{ opacity: 0; transform: scale(.3); }} to {{ opacity: 1; transform: scale(1); }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  @keyframes pulse {{ 0% {{ opacity: .8; transform: scale(.6); }} 100% {{ opacity: 0; transform: scale(2.6); }} }}
  @keyframes nudge {{ 0%, 60%, 100% {{ transform: translateX(0); }} 75% {{ transform: translateX(4px); }} }}
  @keyframes wave {{ 0%, 100% {{ opacity: 0; }} 12% {{ opacity: .55; }} 30% {{ opacity: 0; }} }}
  @keyframes breathe {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.35); }} }}
  @keyframes flame {{ 0%, 100% {{ transform: scaleY(1) rotate(-2deg); }} 50% {{ transform: scaleY(1.15) rotate(3deg); }} }}
{ROLL_KEYFRAMES}
</style>
<g clip-path="url(#card)">
  <rect width="{width}" height="{height}" fill="url(#bg)"/>{glow_el}
  <rect x="-260" y="0" width="200" height="{height}" fill="url(#sweep)" transform="skewX(-20)">
    <animate attributeName="x" values="-260;-260;{width + 300}" keyTimes="0;.55;1" dur="8s" begin="{sweep_delay:.1f}s" repeatCount="indefinite"/>
  </rect>
</g>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="17.5" fill="none" stroke="#FFFFFF" stroke-opacity=".08"/>
{beam_el}
{body}
</svg>"""


def eyebrow(x, y, text):
    return (
        f'<text x="{x}" y="{y}" class="mono in" font-size="11" font-weight="700" '
        f'fill="#4FC39A" letter-spacing="1.4">{escape(text.upper())}</text>'
    )


def live_badge(right, y):
    today = dt.date.today()
    label = f"EN VIVO · {today.day} {MONTHS[today.month - 1]}"
    return (
        f'<g class="in" style="animation-delay:.3s">'
        f'<circle cx="{right - 4}" cy="{y - 4}" r="3.5" fill="#FF5F6D"/>'
        f'<circle class="pulse" cx="{right - 4}" cy="{y - 4}" r="3.5" fill="#FF5F6D"/>'
        f'<text x="{right - 14}" y="{y}" class="mono" font-size="10.5" font-weight="700" fill="#FF9AA2" '
        f'text-anchor="end" letter-spacing="1">{label}</text></g>'
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


# Odómetro: cada dígito es una columna 0-9 que gira hasta su valor.
ROLL_KEYFRAMES = "\n".join(
    f"  @keyframes roll{d} {{ from {{ transform: translateY(0); }} to {{ transform: translateY(calc(-1em * {10 + d} * 1.2)); }} }}"
    for d in range(10)
)
_clip_ids = iter(range(10_000))


def odometer(x, y, value, size, fill="#FFFFFF", delay=0.0, anchor_digits=None):
    text = f"{value:,}"
    digit_w = size * .62
    line_h = size * 1.2
    parts, cx = [], x
    cid = f"odo{next(_clip_ids)}"
    total_w = digit_w * len(text) + 4
    parts.append(
        f'<clipPath id="{cid}"><rect x="{x - 2}" y="{y - size * 1.02:.1f}" width="{total_w:.1f}" height="{size * 1.3:.1f}"/></clipPath>'
        f'<g clip-path="url(#{cid})" class="mono" font-size="{size}" font-weight="800" fill="{fill}" style="font-size:{size}px">'
    )
    n_digits = sum(ch.isdigit() for ch in text)
    k = 0
    for ch in text:
        if ch.isdigit():
            d = int(ch)
            column = "".join(
                f'<text x="{cx:.1f}" y="{y + i * line_h:.1f}">{i % 10}</text>' for i in range(20)
            )
            dur = 1.2 + (n_digits - k) * .25
            parts.append(
                f'<g style="animation: roll{d} {dur:.2f}s cubic-bezier(.15,.85,.25,1) {delay:.2f}s forwards">{column}</g>'
            )
            k += 1
        else:
            parts.append(f'<text x="{cx:.1f}" y="{y}">{escape(ch)}</text>')
        cx += digit_w
    parts.append("</g>")
    return "".join(parts)


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
    body = [eyebrow(28, 42, "En números"), live_badge(377, 42)]
    for i, (value, label) in enumerate(metrics):
        x, y = 28 + (i % 3) * 128, 98 + (i // 3) * 72
        body.append(odometer(x, y, value, 28, delay=.2 + i * .12))
        body.append(
            f'<text x="{x}" y="{y + 22}" class="sans in" style="animation-delay:{.3 + i * .12:.2f}s" font-size="12.5" fill="#7D8FA0">{escape(label)}</text>'
        )
    return svg(405, 220, "Estadísticas de GitHub", "\n".join(body), sweep_delay=1.5)


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
        f'<clipPath id="bar"><rect x="{bar_x}" y="64" width="{bar_w}" height="12" rx="6"/></clipPath>',
        f'<rect x="{bar_x}" y="64" width="{bar_w}" height="12" rx="6" fill="#FFFFFF" fill-opacity=".06"/>',
        f'<g clip-path="url(#bar)"><g class="grow" style="transform-origin:{bar_x}px 0">',
    ]
    x = bar_x
    for _, (size, color) in top:
        w = bar_w * size / grand
        body.append(f'<rect x="{x:.2f}" y="64" width="{w + .6:.2f}" height="12" fill="{color}"/>')
        x += w
    body.append(
        f'</g><rect x="-80" y="64" width="70" height="12" fill="url(#shine)">'
        f'<animate attributeName="x" values="-80;-80;{bar_x + bar_w + 10}" keyTimes="0;.5;1" dur="3.5s" begin="1.5s" repeatCount="indefinite"/></rect></g>'
    )
    for i, (name, (size, color)) in enumerate(top):
        cx, cy = 34 + (i % 2) * 176, 112 + (i // 2) * 34
        pct = 100 * size / grand
        body.append(
            f'<g class="in" style="animation-delay:{350 + i * 90}ms">'
            f'<circle class="breathe" style="animation-delay:{i * .5:.1f}s" cx="{cx}" cy="{cy - 4.5}" r="5" fill="{color}"/>'
            f'<text x="{cx + 14}" y="{cy}" class="sans" font-size="13.5" font-weight="600" fill="#E6EDF3">{escape(name)}</text>'
            f'<text x="{cx + 150}" y="{cy}" class="mono" font-size="12" fill="#7D8FA0" text-anchor="end">{pct:.1f}%</text>'
            f'<rect x="{cx + 14}" y="{cy + 6}" width="{max(2, 136 * pct / 100):.1f}" height="2" rx="1" fill="{color}" opacity=".5" class="grow" style="transform-origin:{cx + 14}px 0"/></g>'
        )
    return svg(405, 220, "Lenguajes más usados", "\n".join(body), sweep_delay=3)


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

    flame = (
        '<g class="flame" transform="translate(0 0)">'
        '<path d="M6 0 C 7 4, 12 6, 12 11 A6 6 0 0 1 0 11 C 0 8, 2 6, 3 4 C 3.5 6, 5 7, 5.5 7 C 5 4, 5 2, 6 0 z" fill="#FF8A4C"/>'
        '<path d="M6 6 C 7 8, 9 9, 9 11.5 A3 3 0 0 1 3 11.5 C 3 10, 4.5 9, 6 6 z" fill="#FFD166"/></g>'
    )
    body = [
        eyebrow(28, 42, "Actividad · último año"),
        live_badge(802, 42),
        odometer(28, 100, cal["totalContributions"], 42, delay=.2),
        '<text x="28" y="124" class="sans in" style="animation-delay:.3s" font-size="13" fill="#7D8FA0">contribuciones</text>',
        f'<g class="in" style="animation-delay:.4s"><g transform="translate(28 150)">{flame}</g>'
        f'<text x="46" y="166" class="sans" font-size="22" font-weight="800" fill="#FFB27A">{current}'
        f'<tspan font-size="13" font-weight="600" fill="#7D8FA0"> {"día" if current == 1 else "días"}</tspan></text>'
        '<text x="28" y="186" class="sans" font-size="12" fill="#7D8FA0">racha actual</text></g>',
        f'<g class="in" style="animation-delay:.5s">'
        f'<text x="148" y="166" class="sans" font-size="22" font-weight="800" fill="#7FD8B4">{longest}'
        f'<tspan font-size="13" font-weight="600" fill="#7D8FA0"> {"día" if longest == 1 else "días"}</tspan></text>'
        '<text x="148" y="186" class="sans" font-size="12" fill="#7D8FA0">racha más larga</text></g>',
    ]

    cell, gap = 13, 3
    grid_x = 802 - len(weeks) * (cell + gap) + gap
    grid_y = 66
    last_month = None
    for wi, week in enumerate(weeks):
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month and wi < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                body.append(
                    f'<text x="{grid_x + wi * (cell + gap)}" y="{grid_y - 9}" class="sans in" font-size="10.5" fill="#5F7385">{MONTHS[first.month - 1]}</text>'
                )
            last_month = first.month
        for day in week["contributionDays"]:
            wd = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7  # domingo = 0
            x, y = grid_x + wi * (cell + gap), grid_y + wd * (cell + gap)
            level = day["contributionLevel"]
            body.append(
                f'<rect class="pop" style="animation-delay:{wi * 30 + wd * 12}ms" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{HEAT[level]}"><title>{day["date"]}: {day["contributionCount"]}</title></rect>'
            )
            if level != "NONE":
                # ola de luz que recorre el calendario de izquierda a derecha
                body.append(
                    f'<rect class="wave" style="animation-delay:{1.5 + wi * .08 + wd * .03:.2f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="#CFFBEA"/>'
                )
    # cursor que recorre el calendario
    top_y, bottom_y = grid_y - 4, grid_y + 7 * (cell + gap) + 1
    body.append(
        f'<rect x="{grid_x - 4}" y="{top_y}" width="2" height="{bottom_y - top_y}" rx="1" fill="#9BF2CF" opacity="0">'
        f'<animate attributeName="x" values="{grid_x - 4};{802 + 2}" dur="5s" begin="1.5s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;.7;.7;0" keyTimes="0;.05;.9;1" dur="5s" begin="1.5s" repeatCount="indefinite"/></rect>'
    )
    legend_y = grid_y + 7 * (cell + gap) + 10
    lx = 802 - 5 * 14 - 30
    body.append(f'<text x="{lx - 8}" y="{legend_y + 9}" class="sans in" font-size="10.5" fill="#5F7385" text-anchor="end">menos</text>')
    for i, color in enumerate(HEAT.values()):
        body.append(f'<rect class="pop" style="animation-delay:{900 + i * 80}ms" x="{lx + i * 14}" y="{legend_y}" width="10" height="10" rx="2.5" fill="{color}"/>')
    body.append(f'<text x="{lx + 5 * 14 + 4}" y="{legend_y + 9}" class="sans in" font-size="10.5" fill="#5F7385">más</text>')
    return svg(830, 225, "Actividad de contribuciones", "\n".join(body))


def repo_card(repo, description, index):
    lang = repo["primaryLanguage"] or {"name": "—", "color": "#7D8FA0"}
    body = [
        '<g class="in" fill="none" stroke="#7FD8B4" stroke-width="1.5" stroke-linejoin="round">'
        '<path d="M30 30 h9 a3 3 0 0 1 3 3 v14 a2.5 2.5 0 0 0 -2.5 -2.5 H30 z"/>'
        '<path d="M30 30 v14.5 M42 33 v14"/></g>',
        f'<text x="54" y="45" class="sans in" font-size="17" font-weight="700" fill="#FFFFFF">{escape(repo["name"])}</text>',
        '<g class="in" style="animation-delay:.1s"><g class="nudge">'
        '<circle cx="379" cy="37" r="12" fill="#FFFFFF" fill-opacity=".05"/>'
        '<path d="M374 37 h10 M380 33 l4 4 -4 4" stroke="#7FD8B4" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g></g>',
    ]
    for i, line in enumerate(wrap(description, 50)[:3]):
        body.append(
            f'<text x="28" y="{80 + i * 21}" class="sans in" style="animation-delay:{.1 + i * .08:.2f}s" font-size="13.5" fill="#B5C6D2">{escape(line)}</text>'
        )
    star = "M0 -6.5 L1.9 -2.1 6.6 -1.7 3 1.4 4.1 6 0 3.6 -4.1 6 -3 1.4 -6.6 -1.7 -1.9 -2.1 z"
    body.append(
        '<g class="in" style="animation-delay:.3s">'
        f'<circle cx="34" cy="150" r="5.5" fill="{lang["color"]}"/>'
        f'<circle class="pulse" cx="34" cy="150" r="5.5" fill="{lang["color"]}" style="animation-duration:3s;animation-delay:{index * .7:.1f}s"/>'
        f'<text x="46" y="155" class="sans" font-size="13" fill="#B5C6D2">{escape(lang["name"])}</text>'
        f'<path transform="translate(148 150)" d="{star}" fill="none" stroke="#FBBF24" stroke-opacity=".8" stroke-width="1.3" stroke-linejoin="round"/>'
        f'<text x="162" y="155" class="sans" font-size="13" fill="#B5C6D2">{repo["stargazerCount"]}</text>'
        "</g>"
    )
    return svg(405, 180, repo["name"], "\n".join(body), glow=False, sweep_delay=index * 1.3, beam=False)


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content.replace("{ROLL_KEYFRAMES}", ROLL_KEYFRAMES))


def main():
    os.makedirs(OUT, exist_ok=True)
    user, repos = fetch_user()
    write("stats.svg", stats_card(user, repos))
    write("langs.svg", langs_card(repos))
    write("activity.svg", activity_card(user))
    for i, repo in enumerate(fetch_featured()):
        write(f"repo-{repo['name']}.svg", repo_card(repo, FEATURED[repo["name"]], i))
    print(f"OK: {len(repos)} repos ({'incluye privados' if PRIVATE else 'solo públicos'})")


if __name__ == "__main__":
    main()
