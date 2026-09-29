"""Generates an animated SVG of a brass time machine that materializes on
contribution squares, takes them, and dematerializes elsewhere."""
import os, json, math, urllib.request

USER = os.environ.get("GH_USER", "S2800-0")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT_FILE", "dist/time-machine.svg")

def fetch_weeks():
    q = {"query": """query($u:String!){user(login:$u){contributionsCollection{
          contributionCalendar{weeks{contributionDays{contributionCount weekday}}}}}}""",
         "variables": {"u": USER}}
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps(q).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

# Ivory / sepia / ink palette
BG, INK, EMPTY = "#faf6ee", "#3b2c1a", "#ece4d4"
LEVELS = [(10, "#3b2c1a"), (6, "#6e5635"), (3, "#a0845a"), (1, "#c9b48a")]
def color(n):
    for t, c in LEVELS:
        if n >= t: return c
    return EMPTY

CELL, GAP, PAD, TOP = 11, 3, 28, 44
STEP = CELL + GAP
MAX_VISITS, HOP, DELAY, REST = 32, 2.6, 1.0, 3.0

def build(weeks):
    W = PAD * 2 + len(weeks) * STEP
    H = TOP + 7 * STEP + PAD
    cells, visits = [], []
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            x, y = PAD + wi * STEP, TOP + d["weekday"] * STEP
            cells.append((x, y, d["contributionCount"]))
            if d["contributionCount"] > 0:
                visits.append(len(cells) - 1)
    if len(visits) > MAX_VISITS:
        visits = [visits[round(i * (len(visits) - 1) / (MAX_VISITS - 1))] for i in range(MAX_VISITS)]
    T = DELAY + len(visits) * HOP + REST
    f = lambda s: f"{min(max(s / T, 0), 1):.4f}"
    visit_start = {ci: DELAY + i * HOP for i, ci in enumerate(visits)}

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    # Time machine symbol: clock rings, roman-style ticks, hourglass, spinning hands
    ticks = "".join(
        f'<line x1="{14*math.sin(a):.2f}" y1="{-14*math.cos(a):.2f}" '
        f'x2="{16.5*math.sin(a):.2f}" y2="{-16.5*math.cos(a):.2f}" stroke="{INK}" stroke-width="{1.4 if k%3==0 else 0.7}"/>'
        for k in range(12) for a in [k * math.pi / 6])
    o.append(f'''<defs><symbol id="tm" viewBox="-24 -24 48 48">
<defs><radialGradient id="glow"><stop offset="0" stop-color="#5b8fd9" stop-opacity="0.55"/>
<stop offset="1" stop-color="#5b8fd9" stop-opacity="0"/></radialGradient></defs>
<circle r="22" fill="url(#glow)"/>
<g fill="none" stroke="#4a7bc8" stroke-linecap="round">
<path d="M0,-21 A21,21 0 0,1 21,0" stroke-width="1.6" opacity="0.8"/>
<path d="M0,21 A21,21 0 0,1 -21,0" stroke-width="1.6" opacity="0.8"/>
<path d="M14,-14 A20,20 0 0,1 14,14" stroke-width="0.8" opacity="0.5"/>
<path d="M-14,14 A20,20 0 0,1 -14,-14" stroke-width="0.8" opacity="0.5"/>
<animateTransform attributeName="transform" type="rotate" from="0" to="-360" dur="1.8s" repeatCount="indefinite"/></g>
<circle r="17.5" fill="{BG}" stroke="{INK}" stroke-width="1.6"/>
<circle r="12" fill="none" stroke="#a0845a" stroke-width="0.8" stroke-dasharray="1 2.2"/>
{ticks}
<path d="M-5,-8 H5 L0.9,0 L5,8 H-5 L-0.9,0 Z" fill="#e8d7ae" stroke="{INK}" stroke-width="0.9"/>
<path d="M-3,6.8 H3 L0,3.2 Z" fill="#a0845a"/>
<g><line x1="0" y1="0" x2="0" y2="-11" stroke="{INK}" stroke-width="1"/>
<line x1="0" y1="0" x2="7" y2="0" stroke="#8b6f47" stroke-width="1"/>
<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="2.5s" repeatCount="indefinite"/></g>
<circle r="1.4" fill="{INK}"/>
</symbol></defs>''')
    o.append(f'<rect width="{W}" height="{H}" fill="{BG}" rx="8" stroke="#c9b48a"/>')
    o.append(f'<text x="{PAD}" y="26" font-family="Georgia, \'Times New Roman\', serif" font-style="italic" '
             f'font-size="14" fill="{INK}">Fig. 1 — Contributions Through Time</text>')
    o.append(f'<text x="{W-PAD}" y="26" text-anchor="end" font-family="Georgia, serif" font-size="11" '
             f'fill="#8b6f47">{USER}</text>')

    for ci, (x, y, n) in enumerate(cells):
        o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{EMPTY}"/>')
        if n == 0: continue
        if ci in visit_start:
            s = visit_start[ci] + 0.55 * HOP  # square is taken while machine is present
            o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color(n)}">'
                     f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{f(s)};{f(s+0.25)};1" '
                     f'dur="{T:.2f}s" repeatCount="indefinite"/></rect>')
        else:
            o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color(n)}"/>')

    # One machine instance per visit, flickering in and out
    pts = [(0, 0), (.08, .35), (.14, .05), (.22, .6), (.29, .2), (.37, .85), (.43, .45),
           (.50, 1), (.62, 1), (.68, .55), (.74, .8), (.81, .3), (.87, .5), (.93, .1), (1.0, 0)]
    for ci in visits:
        x, y, _ = cells[ci]
        s = visit_start[ci]
        kt = ["0"] + [f(s + p * HOP) for p, _ in pts] + ["1"]
        vals = ["0"] + [str(v) for _, v in pts] + ["0"]
        cx, cy = x + CELL / 2, y + CELL / 2
        o.append(f'<use xlink:href="#tm" href="#tm" x="{cx-21:.1f}" y="{cy-21:.1f}" width="42" height="42" opacity="0">'
                 f'<animate attributeName="opacity" values="{";".join(vals)}" keyTimes="{";".join(kt)}" '
                 f'dur="{T:.2f}s" repeatCount="indefinite"/></use>')
        for k, lag in enumerate((0.0, 0.18, 0.36)):
            t0 = s + (0.46 + lag) * HOP
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="none" stroke="#4a7bc8" stroke-width="{1.4-0.35*k:.2f}" opacity="0">'
                     f'<animate attributeName="r" values="4;4;30;30" keyTimes="0;{f(t0)};{f(t0+0.9)};1" dur="{T:.2f}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0;0;0.7;0;0" keyTimes="0;{f(t0)};{f(t0+0.05)};{f(t0+0.9)};1" dur="{T:.2f}s" repeatCount="indefinite"/></circle>')
    o.append("</svg>")
    return "\n".join(o)

if __name__ == "__main__":
    import random
    if TOKEN:
        weeks = fetch_weeks()
    else:  # demo data for local preview
        random.seed(3)
        weeks = [{"contributionDays": [{"weekday": d, "contributionCount": random.choice([0,0,0,1,2,4,7,11])}
                  for d in range(7)]} for _ in range(53)]
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    open(OUT, "w").write(build(weeks))
    print("wrote", OUT)
