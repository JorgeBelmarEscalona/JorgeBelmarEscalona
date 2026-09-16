"""Genera las ilustraciones estáticas del perfil en versión clara y oscura.

    python3 scripts/build_assets.py   ->  assets/<nombre>-light.svg / -dark.svg

Cada SVG trae una media query: cuando la imagen se muestra angosta (celular)
agranda los textos y oculta los detalles que no se alcanzarían a leer.
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "light": {
        "text": "#1F2328", "muted": "#656D76", "faint": "#D0D7DE", "grid": "#EAEEF2",
        "surface": "#F6F8FA", "bg": "#FFFFFF",
        "green": "#2F7A5F", "green_soft": "#D8EEE4",
        "blue": "#2F6DB5", "blue_soft": "#DCE8F6",
        "amber": "#C77D12", "amber_soft": "#F8E7C9",
        "red": "#C8463D",
    },
    "dark": {
        "text": "#E6EDF3", "muted": "#8B949E", "faint": "#30363D", "grid": "#1C2129",
        "surface": "#161B22", "bg": "#0D1117",
        "green": "#5BB08F", "green_soft": "#17332A",
        "blue": "#6CA0DC", "blue_soft": "#172A40",
        "amber": "#E0A040", "amber_soft": "#3A2A12",
        "red": "#E5736A",
    },
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


# ─────────────────────────── utilidades ───────────────────────────

def smooth_closed(points):
    """Catmull-Rom cerrado -> path cúbico."""
    n = len(points)
    d = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(n):
        p0, p1, p2, p3 = points[i - 1], points[i], points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + " Z"


def contours(cx, cy, rings, seed=7):
    rnd = random.Random(seed)
    phases = [rnd.uniform(0, math.tau) for _ in range(4)]
    paths = []
    for k in range(rings):
        base = 16 + k * 17
        pts = []
        for j in range(28):
            t = j / 28 * math.tau
            wobble = (
                .16 * math.sin(2 * t + phases[0] + k * .15)
                + .09 * math.sin(3 * t + phases[1] - k * .1)
                + .05 * math.sin(5 * t + phases[2])
            )
            r = base * (1 + wobble)
            pts.append((cx + r * math.cos(t) * 1.35, cy + r * math.sin(t) * .8))
        paths.append(smooth_closed(pts))
    return paths


def text_width(s, size):
    return len(s) * size * .56


def chips(items, c, x, y):
    out, cx = [], x
    for label in items:
        w = text_width(label, 13) + 22
        out.append(
            f'<rect x="{cx:.0f}" y="{y}" width="{w:.0f}" height="26" rx="13" fill="{c["surface"]}" stroke="{c["faint"]}"/>'
            f'<text x="{cx + w / 2:.0f}" y="{y + 17.5}" text-anchor="middle" font-size="13" fill="{c["muted"]}">{label}</text>'
        )
        cx += w + 8
    return "".join(out)


def card(c, height, name, tagline, stack, mobile_stack, scene, label, accent):
    """Tarjeta de proyecto: encabezado, escena animada y tecnologías."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="830" height="{height}" viewBox="0 0 830 {height}" role="img" aria-label="{label}">
<style>
  text {{ font-family: {SANS}; }}
  .mobile {{ display: none; }}
  @media (max-width: 560px) {{
    .name {{ font-size: 52px; }}
    .tagline {{ display: none; }}
    .chips {{ display: none; }}
    .mobile {{ display: inline; font-size: 27px; }}
  }}
{scene["css"]}
</style>
<rect x="1" y="1" width="828" height="{height - 2}" rx="14" fill="{c['bg']}" stroke="{c['faint']}"/>
<text class="name" x="34" y="66" font-size="30" font-weight="700" letter-spacing="-.6" fill="{c['text']}">{name}</text>
<text class="tagline" x="35" y="94" font-size="16" fill="{c['muted']}">{tagline}</text>
<circle cx="796" cy="52" r="5" fill="{accent}"/>
<circle class="live" cx="796" cy="52" r="5" fill="none" stroke="{accent}" stroke-width="1.5"/>
{scene["svg"]}
<g class="chips">{chips(stack, c, 34, height - 44)}</g>
<text class="mobile" x="35" y="{height - 22}" fill="{c['muted']}">{mobile_stack}</text>
</svg>
"""


LIVE_CSS = """
  .live { transform-box: fill-box; transform-origin: center; animation: live 2.6s ease-out infinite; }
  @keyframes live { 0% { opacity: .8; transform: scale(1); } 80%, 100% { opacity: 0; transform: scale(2.6); } }
"""


def phone_frame(c, x, y):
    return (
        f'<rect x="{x}" y="{y}" width="104" height="172" rx="16" fill="{c["surface"]}" stroke="{c["faint"]}" stroke-width="1.5"/>'
        f'<rect x="{x + 40}" y="{y + 8}" width="24" height="5" rx="2.5" fill="{c["faint"]}"/>'
    )


# ─────────────────────────── portada ───────────────────────────

def hero(c):
    cx, cy = 650, 118
    rings = contours(cx, cy, 11)
    ring_els = []
    for i, d in enumerate(rings):
        major = i % 4 == 3
        ring_els.append(
            f'<path class="ring" style="animation-delay:-{i * 1.1:.1f}s" d="{d}" '
            f'fill="{c["green"]}" fill-opacity="{max(0, .05 - i * .004):.3f}" '
            f'stroke="{c["green"] if major else c["faint"]}" stroke-width="{1.3 if major else 1}" '
            f'stroke-opacity="{.6 if major else 1}"/>'
        )
    survey = rings[6]
    words = ["equipos en terreno", "logística y despacho", "inspección y calidad"]
    word_els = "".join(
        f'<text class="word" style="animation-delay:{i * 4}s" x="46" y="154" font-size="21" fill="{c["muted"]}">'
        f'Software para <tspan fill="{c["text"]}" font-weight="600">{w}</tspan></text>'
        for i, w in enumerate(words)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="830" height="230" viewBox="0 0 830 230" role="img" aria-label="Jorge Belmar — Software para equipos en terreno">
<defs>
  <linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="420" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="m"><rect width="830" height="230" fill="url(#fade)"/></mask>
  <path id="survey" d="{survey}"/>
</defs>
<style>
  text {{ font-family: {SANS}; }}
  .up {{ opacity: 0; animation: up 1s cubic-bezier(.2,.7,.2,1) forwards; }}
  @keyframes up {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}
  .word {{ opacity: 0; animation: word 12s infinite; }}
  @keyframes word {{ 0% {{ opacity: 0; }} 4%, 30% {{ opacity: 1; }} 34%, 100% {{ opacity: 0; }} }}
  .rings {{ transform-origin: {cx}px {cy}px; animation: drift 40s ease-in-out infinite alternate; }}
  @keyframes drift {{ from {{ transform: rotate(-3deg); }} to {{ transform: rotate(4deg) translateX(-10px); }} }}
  .ring {{ transform-origin: {cx}px {cy}px; animation: breathe 9s ease-in-out infinite; }}
  @keyframes breathe {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.04); }} }}
  .line {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 1.6s cubic-bezier(.3,.6,.2,1) .7s forwards; }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  @media (max-width: 560px) {{
    .name {{ font-size: 104px; letter-spacing: -3px; }}
    .words {{ transform: translateY(58px); }}
    .word {{ font-size: 34px; }}
    .line {{ display: none; }}
    .topo {{ opacity: .45; }}
  }}
</style>

<g class="topo" mask="url(#m)">
  <g class="rings">
    {''.join(ring_els)}
    <path d="{survey}" fill="none" stroke="{c['green']}" stroke-width="1.8" pathLength="100" stroke-dasharray="14 86" stroke-linecap="round">
      <animate attributeName="stroke-dashoffset" values="0;-100" dur="24s" repeatCount="indefinite"/>
    </path>
    <g>
      <animateMotion dur="24s" repeatCount="indefinite" keyPoints="0.14;1.14" keyTimes="0;1" calcMode="linear"><mpath href="#survey"/></animateMotion>
      <circle r="4.5" fill="{c['bg']}" stroke="{c['green']}" stroke-width="2"/>
    </g>
  </g>
</g>

<text class="up name" x="44" y="104" font-size="54" font-weight="700" letter-spacing="-1.8" fill="{c['text']}">Jorge Belmar</text>
<g class="words"><g class="up" style="animation-delay:.2s">{word_els}</g></g>
<path class="line" d="M46 182 H126" stroke="{c['green']}" stroke-width="3" stroke-linecap="round" pathLength="1"/>
</svg>
"""


# ─────────────────────────── Gastrack ───────────────────────────

def gastrack(c):
    # Teléfono escaneando un cilindro (ciclo 4 s)
    px, py = 34, 116
    phone = f"""
{phone_frame(c, px, py)}
<rect x="{px + 10}" y="{py + 22}" width="84" height="138" rx="8" fill="{c['grid']}"/>
<rect x="{px + 40}" y="{py + 58}" width="24" height="56" rx="11" fill="{c['blue']}" opacity=".85"/>
<rect x="{px + 46}" y="{py + 50}" width="12" height="9" rx="2" fill="{c['muted']}"/>
<rect x="{px + 40}" y="{py + 76}" width="24" height="9" fill="{c['bg']}" opacity=".55"/>
<g fill="none" stroke="{c['text']}" stroke-width="2.2" stroke-linecap="round">
  <path d="M{px + 24} {py + 52} v-10 h10"/><path d="M{px + 70} {py + 42} h10 v10"/>
  <path d="M{px + 80} {py + 116} v10 h-10"/><path d="M{px + 34} {py + 126} h-10 v-10"/>
</g>
<rect class="scan" x="{px + 26}" y="{py + 46}" width="52" height="2.5" rx="1.2" fill="{c['green']}"/>
<g class="ok"><circle cx="{px + 52}" cy="{py + 86}" r="17" fill="{c['green']}"/>
  <path d="M{px + 44} {py + 86} l6 6 l10 -12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></g>
<rect x="{px + 22}" y="{py + 142}" width="60" height="10" rx="5" fill="{c['faint']}"/>
"""

    # Mapa con camión (ciclo 12 s)
    mx, my, mw, mh = 162, 116, 360, 172
    route = f"M{mx + 30} {my + 142} H{mx + 150} V{my + 92} H{mx + 262} V{my + 38} H{mx + 330}"
    kp, kt = "0;.34;.34;.66;.66;1;1", "0;.22;.30;.52;.60;.85;1"
    dash = ";".join(f"{1 - float(k):.2f}" for k in kp.split(";"))
    streets = "".join(
        f'<path d="{d}" stroke="{c["grid"]}" stroke-width="9" stroke-linecap="round"/>'
        for d in (
            f"M{mx} {my + 142} H{mx + mw}", f"M{mx} {my + 92} H{mx + mw}", f"M{mx} {my + 38} H{mx + mw}",
            f"M{mx + 150} {my} V{mh + my}", f"M{mx + 262} {my} V{mh + my}", f"M{mx + 70} {my} V{mh + my}",
        )
    )
    pins = []
    for (x, y, t) in ((mx + 150, my + 92, .22), (mx + 262, my + 38, .52), (mx + 330, my + 38, .85)):
        pins.append(
            f'<g transform="translate({x} {y})">'
            f'<circle r="4" fill="{c["bg"]}" stroke="{c["amber"]}" stroke-width="2"/>'
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{t:.2f};{t + .03:.2f};.97;1" dur="12s" repeatCount="indefinite"/>'
            f'<path d="M0 -4 c-7 -9 -8 -12 -8 -15 a8 8 0 0 1 16 0 c0 3 -1 6 -8 15 z" fill="{c["amber"]}"/>'
            f'<circle cx="0" cy="-19" r="3" fill="{c["bg"]}"/></g></g>'
        )
    truck_map = f"""
<clipPath id="map"><rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="12"/></clipPath>
<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="12" fill="{c['surface']}" stroke="{c['faint']}" stroke-width="1.5"/>
<g clip-path="url(#map)">
  {streets}
  <rect x="{mx + 84}" y="{my + 12}" width="52" height="60" rx="4" fill="{c['green_soft']}"/>
  <rect x="{mx + 176}" y="{my + 112}" width="72" height="44" rx="4" fill="{c['blue_soft']}"/>
  <path id="route" d="{route}" fill="none" stroke="{c['faint']}" stroke-width="3" stroke-dasharray="1 6" stroke-linecap="round"/>
  <path d="{route}" fill="none" stroke="{c['blue']}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1">
    <animate attributeName="stroke-dashoffset" values="{dash}" keyTimes="{kt}" dur="12s" repeatCount="indefinite"/>
  </path>
  <g transform="translate({mx + 30} {my + 142})"><rect x="-10" y="-10" width="20" height="20" rx="5" fill="{c['blue']}"/><path d="M-5 4 v-5 l5 -4 l5 4 v5" fill="none" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/></g>
  {''.join(pins)}
  <g>
    <animateMotion dur="12s" repeatCount="indefinite" keyPoints="{kp}" keyTimes="{kt}" calcMode="linear" rotate="auto"><mpath href="#route"/></animateMotion>
    <g transform="translate(-14 -8)">
      <rect x="0" y="1" width="19" height="14" rx="2.5" fill="{c['text']}"/>
      <path d="M20 3 h4 a3 3 0 0 1 3 3 v4 a3 3 0 0 1 -3 3 h-4 z" fill="{c['blue']}"/>
    </g>
  </g>
</g>
"""

    # Panel con datos que cambian
    dx, dy, dw, dh = 538, 116, 260, 172
    bars = []
    for i, (color, vals, dur) in enumerate((
        (c["green"], "78;90;84;96;78", "9s"),
        (c["amber"], "36;26;40;30;36", "7s"),
        (c["red"], "14;20;10;17;14", "8s"),
    )):
        y = dy + 38 + i * 26
        bars.append(
            f'<circle cx="{dx + 134}" cy="{y + 4}" r="4" fill="{color}"/>'
            f'<rect x="{dx + 146}" y="{y}" width="96" height="8" rx="4" fill="{c["grid"]}"/>'
            f'<rect x="{dx + 146}" y="{y}" width="{vals.split(";")[0]}" height="8" rx="4" fill="{color}">'
            f'<animate attributeName="width" values="{vals}" dur="{dur}" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/></rect>'
        )
    spark = f"M{dx + 20} {dy + 152} l28 -8 l28 4 l28 -14 l28 6 l28 -16 l28 2 l28 -10 l28 4"
    dcx, dcy = dx + 64, dy + 72
    dashboard = f"""
<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" rx="12" fill="{c['surface']}" stroke="{c['faint']}" stroke-width="1.5"/>
<g transform="rotate(-90 {dcx} {dcy})" fill="none" stroke-width="11">
  <circle cx="{dcx}" cy="{dcy}" r="34" stroke="{c['grid']}"/>
  <circle class="seg" cx="{dcx}" cy="{dcy}" r="34" stroke="{c['green']}" pathLength="100" stroke-dasharray="62 38"/>
  <circle class="seg" style="animation-delay:.25s" cx="{dcx}" cy="{dcy}" r="34" stroke="{c['amber']}" pathLength="100" stroke-dasharray="24 76" stroke-dashoffset="-63"/>
  <circle class="seg" style="animation-delay:.5s" cx="{dcx}" cy="{dcy}" r="34" stroke="{c['red']}" pathLength="100" stroke-dasharray="11 89" stroke-dashoffset="-88"/>
</g>
{''.join(bars)}
<path class="spark" d="{spark}" fill="none" stroke="{c['blue']}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/>
"""

    # Lectura del escáner que viaja al panel
    packet = f"""
<circle r="5" fill="{c['green']}" opacity="0">
  <animateMotion dur="4s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;.62;.95;1" calcMode="linear"
    path="M{px + 104} {py + 70} C 300 70, 460 70, {dcx} {dy + 30}"/>
  <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.62;.66;.92;.95;1" dur="4s" repeatCount="indefinite"/>
</circle>"""

    css = LIVE_CSS + """
  .scan { animation: scan 4s ease-in-out infinite; }
  @keyframes scan { 0% { transform: translateY(0); opacity: 1; } 25% { transform: translateY(74px); } 50% { transform: translateY(0); opacity: 1; } 55%, 100% { opacity: 0; } }
  .ok { transform-box: fill-box; transform-origin: center; animation: ok 4s cubic-bezier(.3,1.5,.5,1) infinite; }
  @keyframes ok { 0%, 52% { opacity: 0; transform: scale(.4); } 60%, 90% { opacity: 1; transform: scale(1); } 100% { opacity: 0; transform: scale(1); } }
  .seg { animation: seg 1.4s cubic-bezier(.2,.7,.2,1) both; }
  @keyframes seg { from { stroke-dasharray: 0 100; } }
  .spark { stroke-dasharray: 1; animation: spark 7s ease-in-out infinite; }
  @keyframes spark { 0% { stroke-dashoffset: 1; } 45%, 85% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: -1; } }
"""
    scene = {"css": css, "svg": phone + truck_map + dashboard + packet}
    return card(
        c, 340, "Gastrack", "Trazabilidad de cilindros de gas, desde el escaneo hasta la entrega",
        ["PHP", "MySQL", "Kotlin", "Jetpack Compose", "ML Kit", "Leaflet", "Docker"],
        "PHP · Kotlin · ML Kit · Leaflet", scene, "Gastrack", c["blue"],
    )


# ─────────────────────────── Pangea NC ───────────────────────────

def pangea(c):
    px, py = 34, 116
    phone = f"""
{phone_frame(c, px, py)}
<rect x="{px + 10}" y="{py + 22}" width="84" height="138" rx="8" fill="{c['bg']}"/>
<rect x="{px + 18}" y="{py + 30}" width="68" height="46" rx="6" fill="{c['green_soft']}"/>
<path d="M{px + 24} {py + 70} l14 -16 l10 10 l8 -7 l14 13 z" fill="{c['green']}" opacity=".7"/>
<circle cx="{px + 72}" cy="{py + 42}" r="5" fill="{c['amber']}" opacity=".8"/>
<rect class="flash" x="{px + 18}" y="{py + 30}" width="68" height="46" rx="6" fill="#fff"/>
<rect x="{px + 18}" y="{py + 88}" width="68" height="7" rx="3.5" fill="{c['grid']}"/>
<rect class="f1" x="{px + 18}" y="{py + 88}" width="54" height="7" rx="3.5" fill="{c['muted']}" opacity=".5"/>
<rect x="{px + 18}" y="{py + 102}" width="68" height="7" rx="3.5" fill="{c['grid']}"/>
<rect class="f2" x="{px + 18}" y="{py + 102}" width="40" height="7" rx="3.5" fill="{c['muted']}" opacity=".5"/>
<rect x="{px + 18}" y="{py + 116}" width="68" height="7" rx="3.5" fill="{c['grid']}"/>
<rect class="f3" x="{px + 18}" y="{py + 116}" width="60" height="7" rx="3.5" fill="{c['muted']}" opacity=".5"/>
<rect class="send" x="{px + 18}" y="{py + 134}" width="68" height="18" rx="9" fill="{c['green']}"/>
"""
    bx, by, bw, bh = 162, 116, 636, 172
    col_w, gap = 200, 8
    columns = [("Abierta", c["amber"]), ("En revisión", c["blue"]), ("Cerrada", c["green"])]
    board = [
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="{c["surface"]}" stroke="{c["faint"]}" stroke-width="1.5"/>'
    ]

    def ticket(x, y, color, w1=110, w2=70):
        return (
            f'<rect x="{x}" y="{y}" width="{col_w - 20}" height="34" rx="6" fill="{c["bg"]}" stroke="{c["faint"]}"/>'
            f'<rect x="{x}" y="{y}" width="4" height="34" rx="2" fill="{color}"/>'
            f'<rect x="{x + 14}" y="{y + 9}" width="{w1}" height="6" rx="3" fill="{c["faint"]}"/>'
            f'<rect x="{x + 14}" y="{y + 21}" width="{w2}" height="5" rx="2.5" fill="{c["grid"]}"/>'
        )

    col_x = []
    for i, (label, color) in enumerate(columns):
        x = bx + 10 + i * (col_w + gap)
        col_x.append(x + 10)
        board.append(
            f'<circle cx="{x + 10}" cy="{by + 22}" r="4.5" fill="{color}"/>'
            f'<text x="{x + 22}" y="{by + 27}" font-size="13" font-weight="600" fill="{c["muted"]}">{label}</text>'
            f'<rect x="{x}" y="{by + 38}" width="{col_w}" height="{bh - 48}" rx="8" fill="{c["grid"]}" opacity=".7"/>'
        )
    board.append(ticket(col_x[0], by + 46, c["amber"], 120, 60))
    board.append(ticket(col_x[0], by + 86, c["amber"], 90, 80))
    board.append(ticket(col_x[1], by + 46, c["blue"], 100, 70))
    board.append(ticket(col_x[2], by + 46, c["green"], 130, 50))
    board.append(ticket(col_x[2], by + 86, c["green"], 80, 64))

    step = col_w + gap
    ty = by + 126
    mover = f"""
<g class="mover">
  <rect x="{col_x[0]}" y="{ty}" width="{col_w - 20}" height="34" rx="6" fill="{c['bg']}" stroke="{c['muted']}" stroke-opacity=".5"/>
  <rect class="st-a" x="{col_x[0]}" y="{ty}" width="4" height="34" rx="2" fill="{c['amber']}"/>
  <rect class="st-b" x="{col_x[0]}" y="{ty}" width="4" height="34" rx="2" fill="{c['blue']}"/>
  <rect class="st-c" x="{col_x[0]}" y="{ty}" width="4" height="34" rx="2" fill="{c['green']}"/>
  <rect x="{col_x[0] + 14}" y="{ty + 9}" width="96" height="6" rx="3" fill="{c['text']}" opacity=".55"/>
  <rect x="{col_x[0] + 14}" y="{ty + 21}" width="60" height="5" rx="2.5" fill="{c['faint']}"/>
  <g class="st-c"><circle cx="{col_x[0] + col_w - 38}" cy="{ty + 17}" r="8" fill="{c['green']}"/>
    <path d="M{col_x[0] + col_w - 42} {ty + 17} l3 3 l5 -6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g>
</g>
<circle r="5" fill="{c['green']}" opacity="0">
  <animateMotion dur="12s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;.3;.42;1" calcMode="linear"
    path="M{px + 86} {py + 143} C {px + 150} {py + 143}, {col_x[0] - 30} {ty + 17}, {col_x[0] + 40} {ty + 17}"/>
  <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.3;.32;.4;.42;1" dur="12s" repeatCount="indefinite"/>
</circle>
"""
    css = LIVE_CSS + f"""
  .flash {{ opacity: 0; animation: flash 12s infinite; }}
  @keyframes flash {{ 0%, 4% {{ opacity: 0; }} 5% {{ opacity: .9; }} 9%, 100% {{ opacity: 0; }} }}
  .f1, .f2, .f3 {{ transform-box: fill-box; transform: scaleX(0); animation: fill1 12s infinite; }}
  .f2 {{ animation-name: fill2; }} .f3 {{ animation-name: fill3; }}
  @keyframes fill1 {{ 0%, 10% {{ transform: scaleX(0); }} 16%, 94% {{ transform: scaleX(1); }} 100% {{ transform: scaleX(0); }} }}
  @keyframes fill2 {{ 0%, 15% {{ transform: scaleX(0); }} 20%, 94% {{ transform: scaleX(1); }} 100% {{ transform: scaleX(0); }} }}
  @keyframes fill3 {{ 0%, 19% {{ transform: scaleX(0); }} 25%, 94% {{ transform: scaleX(1); }} 100% {{ transform: scaleX(0); }} }}
  .send {{ transform-box: fill-box; transform-origin: center; animation: send 12s infinite; }}
  @keyframes send {{ 0%, 27% {{ transform: scale(1); }} 29% {{ transform: scale(.9); }} 32%, 100% {{ transform: scale(1); }} }}
  .mover {{ opacity: 0; animation: mover 12s cubic-bezier(.5,0,.3,1) infinite; }}
  @keyframes mover {{
    0%, 41% {{ opacity: 0; transform: translate(0, 8px); }}
    45%, 58% {{ opacity: 1; transform: translate(0, 0); }}
    66%, 76% {{ opacity: 1; transform: translate({step}px, 0); }}
    84%, 95% {{ opacity: 1; transform: translate({step * 2}px, 0); }}
    100% {{ opacity: 0; transform: translate({step * 2}px, 0); }}
  }}
  .st-a {{ animation: sta 12s infinite; }} .st-b {{ opacity: 0; animation: stb 12s infinite; }} .st-c {{ opacity: 0; animation: stc 12s infinite; }}
  @keyframes sta {{ 0%, 62% {{ opacity: 1; }} 64%, 100% {{ opacity: 0; }} }}
  @keyframes stb {{ 0%, 62% {{ opacity: 0; }} 64%, 80% {{ opacity: 1; }} 82%, 100% {{ opacity: 0; }} }}
  @keyframes stc {{ 0%, 80% {{ opacity: 0; }} 82%, 100% {{ opacity: 1; }} }}
"""
    scene = {"css": css, "svg": phone + "".join(board) + mover}
    return card(
        c, 340, "Pangea NC", "No conformidades reportadas en terreno y cerradas en el panel",
        ["PHP", "JavaScript", "PWA", "Kotlin", "Swift", "SwiftUI"],
        "PHP · PWA · Kotlin · Swift", scene, "Pangea NC", c["green"],
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    for theme, colors in THEMES.items():
        for name, fn in (("hero", hero), ("gastrack", gastrack), ("pangea", pangea)):
            with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w", encoding="utf-8") as f:
                f.write(fn(colors))
    print("OK")


if __name__ == "__main__":
    main()
