"""Genera las ilustraciones estáticas del perfil en versión clara y oscura.

    python3 scripts/build_assets.py   ->  assets/<nombre>-light.svg / -dark.svg

Las ilustraciones no llevan texto pequeño: así escalan bien en pantallas
angostas. El texto del perfil vive en el README.
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "light": {
        "text": "#1F2328", "muted": "#656D76", "faint": "#D0D7DE", "grid": "#E4E8EC",
        "surface": "#F6F8FA", "bg": "#FFFFFF",
        "accent": "#2F7A5F", "accent_soft": "#CFE8DC", "blue": "#3B6EA5", "amber": "#B7791F",
    },
    "dark": {
        "text": "#E6EDF3", "muted": "#8B949E", "faint": "#30363D", "grid": "#21262D",
        "surface": "#161B22", "bg": "#0D1117",
        "accent": "#5BB08F", "accent_soft": "#1B3B30", "blue": "#6CA0DC", "amber": "#D69E2E",
    },
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


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


def hero(c):
    cx, cy = 650, 118
    rings = contours(cx, cy, 11)
    ring_els = []
    for i, d in enumerate(rings):
        major = i % 4 == 3
        ring_els.append(
            f'<path class="ring" style="animation-delay:-{i * 1.1:.1f}s" d="{d}" fill="none" '
            f'stroke="{c["muted"] if major else c["faint"]}" stroke-width="{1.3 if major else 1}" '
            f'stroke-opacity="{.55 if major else 1}"/>'
        )
    survey = rings[6]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="830" height="230" viewBox="0 0 830 230" role="img" aria-label="Jorge Belmar">
<defs>
  <linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="420" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="m"><rect width="830" height="230" fill="url(#fade)"/></mask>
  <path id="survey" d="{survey}"/>
</defs>
<style>
  .up {{ opacity: 0; animation: up 1s cubic-bezier(.2,.7,.2,1) forwards; }}
  @keyframes up {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}
  .rings {{ transform-origin: {cx}px {cy}px; animation: drift 40s ease-in-out infinite alternate; }}
  @keyframes drift {{ from {{ transform: rotate(-3deg); }} to {{ transform: rotate(4deg) translateX(-10px); }} }}
  .ring {{ transform-origin: {cx}px {cy}px; animation: breathe 9s ease-in-out infinite; }}
  @keyframes breathe {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.035); }} }}
  .line {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 1.6s cubic-bezier(.3,.6,.2,1) .7s forwards; }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  /* En pantallas angostas la imagen se escala: se agranda el texto para que siga legible. */
  @media (max-width: 560px) {{
    .name {{ font-size: 104px; letter-spacing: -3px; }}
    .role {{ font-size: 40px; }}
    .role-y {{ transform: translateY(40px); }}
    .line {{ display: none; }}
    .topo {{ opacity: .45; }}
  }}
</style>

<g class="topo" mask="url(#m)">
  <g class="rings">
    {''.join(ring_els)}
    <path d="{survey}" fill="none" stroke="{c['accent']}" stroke-width="1.6" pathLength="100" stroke-dasharray="14 86" stroke-linecap="round">
      <animate attributeName="stroke-dashoffset" values="0;-100" dur="24s" repeatCount="indefinite"/>
    </path>
    <g>
      <animateMotion dur="24s" repeatCount="indefinite" keyPoints="0.14;1.14" keyTimes="0;1" calcMode="linear"><mpath href="#survey"/></animateMotion>
      <circle r="4" fill="{c['bg']}" stroke="{c['accent']}" stroke-width="1.8"/>
    </g>
  </g>
</g>

<g font-family="{SANS}">
  <text class="up name" x="44" y="112" font-size="54" font-weight="700" letter-spacing="-1.8" fill="{c['text']}">Jorge Belmar</text>
  <g class="role-y"><text class="up role" style="animation-delay:.18s" x="46" y="154" font-size="21" fill="{c['muted']}">Software para operaciones en terreno</text></g>
</g>
<path class="line" d="M46 180 H126" stroke="{c['accent']}" stroke-width="3" stroke-linecap="round" pathLength="1"/>
</svg>
"""


def gastrack(c):
    route = "M60 112 C 150 112, 170 62, 260 66 S 380 128, 470 110 S 600 48, 690 70 S 760 108, 780 104"
    # (keyPoint, keyTime) de cada parada: el camión se detiene en ellas.
    stops = [(60, 112, 0.0, 0.0), (260, 66, .30, .26), (470, 110, .58, .56), (780, 104, 1.0, .9)]
    key_points = "0;.30;.30;.58;.58;1;1"
    key_times = "0;.20;.26;.50;.56;.90;1"
    dash_values = ";".join(f"{1 - float(k):.2f}" for k in key_points.split(";"))
    stop_els = []
    for i, (x, y, _, t) in enumerate(stops):
        if i == 0:
            fill = f'fill="{c["accent"]}"'
            anim = ""
        else:
            fill = f'fill="{c["bg"]}"'
            anim = (
                f'<animate attributeName="fill" values="{c["bg"]};{c["accent"]};{c["accent"]};{c["bg"]}" '
                f'keyTimes="0;{t:.2f};.97;1" calcMode="discrete" dur="16s" repeatCount="indefinite"/>'
            )
        stop_els.append(
            f'<circle cx="{x}" cy="{y}" r="6" {fill} stroke="{c["accent"]}" stroke-width="2">{anim}</circle>'
        )
        if i:
            stop_els.append(
                f'<circle cx="{x}" cy="{y}" r="6" fill="none" stroke="{c["accent"]}" opacity="0">'
                f'<animate attributeName="r" values="6;6;20;20" keyTimes="0;{t:.2f};{min(t + .08, .99):.2f};1" dur="16s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;.6;0;0" keyTimes="0;{t:.2f};{min(t + .08, .99):.2f};1" dur="16s" repeatCount="indefinite"/></circle>'
            )

    def cylinder(x, y):
        return (
            f'<g fill="none" stroke="{c["muted"]}" stroke-width="1.4">'
            f'<rect x="{x}" y="{y}" width="10" height="20" rx="4"/><path d="M{x + 3} {y} v-3 h4 v3"/></g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="830" height="170" viewBox="0 0 830 170" role="img" aria-label="Ruta de despacho de cilindros">
<defs>
  <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{c['grid']}"/></pattern>
  <radialGradient id="vg" cx=".5" cy=".5" r=".6"><stop offset=".55" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
  <mask id="m"><rect width="830" height="170" fill="url(#vg)"/></mask>
  <path id="route" d="{route}"/>
</defs>
<rect width="830" height="170" fill="url(#dots)" mask="url(#m)"/>

<!-- bodega -->
<g fill="none" stroke="{c['muted']}" stroke-width="1.4" stroke-linejoin="round">
  <path d="M44 96 V80 L60 70 L76 80 V96 Z"/><path d="M54 96 v-9 h12 v9"/>
</g>
{cylinder(252, 28)}{cylinder(266, 28)}
{cylinder(470 - 5, 128)}
<g fill="none" stroke="{c['muted']}" stroke-width="1.4" stroke-linecap="round"><path d="M780 90 v-26"/><path d="M780 64 h16 l-4 5 l4 5 h-16" stroke-linejoin="round"/></g>

<use href="#route" fill="none" stroke="{c['faint']}" stroke-width="3" stroke-linecap="round"/>
<use href="#route" fill="none" stroke="{c['accent']}" stroke-width="3" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1">
  <animate attributeName="stroke-dashoffset" values="{dash_values}" keyTimes="{key_times}" dur="16s" repeatCount="indefinite"/>
</use>
{''.join(stop_els)}

<g>
  <animateMotion dur="16s" repeatCount="indefinite" keyPoints="{key_points}" keyTimes="{key_times}" calcMode="spline"
    keySplines=".4 0 .6 1;0 0 1 1;.4 0 .6 1;0 0 1 1;.4 0 .6 1;0 0 1 1"><mpath href="#route"/></animateMotion>
  <g transform="translate(-16 -24)">
    <rect x="0" y="4" width="21" height="13" rx="2.5" fill="{c['text']}"/>
    <path d="M22 8 h6 l5 5 v4 h-11 z" fill="{c['text']}"/>
    <rect x="25" y="10" width="4" height="3" rx=".8" fill="{c['bg']}"/>
    <circle cx="7" cy="18" r="3" fill="{c['bg']}" stroke="{c['text']}" stroke-width="1.6"/>
    <circle cx="26" cy="18" r="3" fill="{c['bg']}" stroke="{c['text']}" stroke-width="1.6"/>
  </g>
</g>
</svg>
"""


def pangea(c):
    def phone(x, y, notch):
        top = (
            f'<rect x="{x + 17}" y="{y + 5}" width="12" height="3" rx="1.5" fill="{c["faint"]}"/>' if notch
            else f'<circle cx="{x + 23}" cy="{y + 7}" r="1.6" fill="{c["faint"]}"/>'
        )
        return (
            f'<rect x="{x}" y="{y}" width="46" height="88" rx="9" fill="{c["bg"]}" stroke="{c["muted"]}" stroke-width="1.5"/>{top}'
            f'<rect x="{x + 7}" y="{y + 16}" width="32" height="24" rx="3" fill="{c["surface"]}" stroke="{c["faint"]}"/>'
            f'<path d="M{x + 12} {y + 34} l7 -8 l5 5 l3 -3 l7 8" fill="none" stroke="{c["faint"]}" stroke-width="1.3" stroke-linejoin="round"/>'
            f'<rect x="{x + 7}" y="{y + 47}" width="26" height="3" rx="1.5" fill="{c["faint"]}"/>'
            f'<rect x="{x + 7}" y="{y + 55}" width="18" height="3" rx="1.5" fill="{c["faint"]}"/>'
            f'<rect x="{x + 7}" y="{y + 68}" width="32" height="10" rx="5" fill="{c["accent"]}" opacity=".85"/>'
        )

    # Paquetes: salen de cada teléfono y llegan al panel; al llegar aparece una fila.
    wires = [
        ("M88 66 C 240 66, 330 58, 470 76", 0.0),
        ("M152 100 C 290 100, 350 104, 470 100", 4.0),
    ]
    wire_els, packet_els = [], []
    for d, begin in wires:
        wire_els.append(f'<path d="{d}" fill="none" stroke="{c["faint"]}" stroke-width="1.5" stroke-dasharray="3 5"/>')
        packet_els.append(
            f'<rect x="-6" y="-4" width="12" height="8" rx="2" fill="{c["accent"]}" opacity="0">'
            f'<animateMotion dur="8s" begin="{begin}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;.05;.35;1" calcMode="spline" keySplines="0 0 1 1;.4 0 .4 1;0 0 1 1" path="{d}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.05;.33;.36;1" dur="8s" begin="{begin}s" repeatCount="indefinite"/></rect>'
        )

    rows = []
    for i in range(4):
        y = 58 + i * 22
        # estado: pendiente (ámbar) que pasa a cerrado (verde)
        rows.append(
            f'<g><rect x="560" y="{y}" width="{150 - i * 18}" height="5" rx="2.5" fill="{c["faint"]}"/>'
            f'<rect x="560" y="{y + 9}" width="{90 - i * 8}" height="4" rx="2" fill="{c["grid"]}"/>'
            f'<rect x="744" y="{y + 1}" width="28" height="11" rx="5.5" fill="{c["amber"]}" fill-opacity=".85">'
            f'<animate attributeName="fill" values="{c["amber"]};{c["amber"]};{c["accent"]};{c["accent"]}" keyTimes="0;{.3 + i * .15:.2f};{.34 + i * .15:.2f};1" dur="16s" repeatCount="indefinite"/></rect></g>'
        )
    new_row = (
        f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.36;.42;.95;1" dur="8s" repeatCount="indefinite"/>'
        f'<rect x="548" y="34" width="232" height="18" rx="4" fill="{c["accent_soft"]}"/>'
        f'<rect x="560" y="40" width="120" height="5" rx="2.5" fill="{c["accent"]}" opacity=".7"/>'
        f'<circle cx="766" cy="43" r="3.5" fill="{c["accent"]}"/></g>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="830" height="170" viewBox="0 0 830 170" role="img" aria-label="Reportes desde terreno al panel web">
<style>
  .float {{ animation: float 6s ease-in-out infinite; }}
  @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} }}
</style>
<g class="float">{phone(40, 26, notch=False)}</g>
<g class="float" style="animation-delay:-3s">{phone(104, 56, notch=True)}</g>
{''.join(wire_els)}
{''.join(packet_els)}

<rect x="470" y="14" width="320" height="142" rx="10" fill="{c['bg']}" stroke="{c['muted']}" stroke-width="1.5"/>
<path d="M470 30 H790" stroke="{c['faint']}"/>
<g fill="{c['faint']}"><circle cx="483" cy="22" r="3"/><circle cx="494" cy="22" r="3"/><circle cx="505" cy="22" r="3"/></g>
<rect x="480" y="40" width="54" height="106" rx="4" fill="{c['surface']}"/>
<g fill="{c['faint']}"><rect x="488" y="50" width="36" height="4" rx="2"/><rect x="488" y="62" width="28" height="4" rx="2"/><rect x="488" y="74" width="32" height="4" rx="2"/></g>
<rect x="484" y="46" width="3" height="12" rx="1.5" fill="{c['accent']}"/>
{new_row}
{''.join(rows)}
</svg>
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    for theme, colors in THEMES.items():
        for name, fn in (("hero", hero), ("gastrack", gastrack), ("pangea", pangea)):
            with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w", encoding="utf-8") as f:
                f.write(fn(colors))
    print("OK")


if __name__ == "__main__":
    main()
