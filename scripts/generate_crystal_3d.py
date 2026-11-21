#!/usr/bin/env python3
"""
Generate dark and light continuously-animated 3D Phonon Crystal-Lattice Contribution SVGs.
Fetches exact GitHub contribution history via GraphQL (when GITHUB_TOKEN is set in Actions)
with automatic fallback to GitHub's public contributions calendar page.
Pure SVG + CSS @keyframes animations (zero <script>, zero <foreignObject>),
100% compatible with GitHub's camo.githubusercontent.com security proxy.
"""

from __future__ import annotations
import argparse
import datetime as dt
import json
import math
import os
import re
import urllib.request
from pathlib import Path


LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_via_graphql(username: str, token: str) -> tuple[list[list[dict]], int]:
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                contributionLevel
                date
                weekday
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "SuthPhy2Ai-Crystal-Lattice-3D/2.1",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = int(cal["totalContributions"])
    weeks_out: list[list[dict]] = []
    for wk in cal["weeks"]:
        col = []
        for day in wk["contributionDays"]:
            col.append(
                {
                    "date": day["date"],
                    "weekday": int(day["weekday"]),
                    "count": int(day["contributionCount"]),
                    "level": LEVEL_MAP.get(day["contributionLevel"], 0),
                }
            )
        weeks_out.append(col)
    return weeks_out, total


def fetch_via_public_html(username: str) -> tuple[list[list[dict]], int]:
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    counts_by_id: dict[str, int] = {}
    for m in re.finditer(
        r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]+)</tool-tip>',
        html,
    ):
        comp_id, text = m.group(1), m.group(2).strip()
        m_num = re.match(r"(\d+)\s+contribution", text)
        counts_by_id[comp_id] = int(m_num.group(1)) if m_num else 0

    cells_by_week: dict[int, list[dict]] = {}
    for tag in re.findall(r"<td\b[^>]*ContributionCalendar-day[^>]*>", html):
        m_id = re.search(r'id="(contribution-day-component-(\d+)-(\d+))"', tag)
        m_date = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        m_lvl = re.search(r'data-level="(\d)"', tag)
        if not (m_id and m_date and m_lvl):
            continue
        comp_id = m_id.group(1)
        weekday = int(m_id.group(2))
        week_idx = int(m_id.group(3))
        lvl = int(m_lvl.group(1))
        cnt = counts_by_id.get(comp_id, lvl)
        cells_by_week.setdefault(week_idx, []).append(
            {
                "date": m_date.group(1),
                "weekday": weekday,
                "count": cnt,
                "level": lvl,
            }
        )

    weeks_out = []
    total = 0
    for w_idx in sorted(cells_by_week.keys()):
        col = sorted(cells_by_week[w_idx], key=lambda c: c["weekday"])
        total += sum(c["count"] for c in col)
        weeks_out.append(col)
    return weeks_out, total


def lerp_hex(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_crystal_svg(weeks: list[list[dict]], total_contribs: int, mode: str) -> str:
    if mode == "dark":
        pal = {
            "bg1": "#070c18",
            "bg2": "#0d1629",
            "bg3": "#111c35",
            "border": "#1e293b",
            "grid": "#38bdf8",
            "grid_op": "0.045",
            "glow_cyan": "#0ea5e9",
            "glow_violet": "#8b5cf6",
            "subtitle": "#94a3b8",
            "pill_bg": "#101b30",
            "pill_border": "#1e3a5f",
            "pill_text": "#7dd3fc",
            "stat_label": "#64748b",
            "stat_val": "#e2e8f0",
            "stat_hi": "#38bdf8",
            "dot": "#34d399",
            "axis_text": "#64748b",
            "slab_shadow": "rgba(2, 6, 23, 0.65)",
            "base_top": "#122038",
            "base_crest": "#1d3b63",
            "base_left": "#0c1526",
            "base_right": "#080e1c",
            "base_stroke": "#1e3458",
            "halo_top": "#155e75",
            "halo_left": "#0e3f52",
            "halo_right": "#092738",
            "halo_stroke": "#0ea5e9",
            "lvl": {
                1: ("#22d3ee", "#0891b2", "#164e63", "#a5f3fc", "#cffafe"),
                2: ("#38bdf8", "#0284c7", "#0c4a6e", "#bae6fd", "#e0f2fe"),
                3: ("#34d399", "#059669", "#064e3b", "#a7f3d0", "#ecfdf5"),
                4: ("#c084fc", "#7c3aed", "#4c1d95", "#f3e8ff", "#ffffff"),
            },
            "exciton": "#7dd3fc",
            "scan_beam": "#38bdf8",
        }
    else:
        pal = {
            "bg1": "#f8fafc",
            "bg2": "#f1f5f9",
            "bg3": "#eef2ff",
            "border": "#cbd5e1",
            "grid": "#0284c7",
            "grid_op": "0.055",
            "glow_cyan": "#0284c7",
            "glow_violet": "#7c3aed",
            "subtitle": "#475569",
            "pill_bg": "#e0f2fe",
            "pill_border": "#bae6fd",
            "pill_text": "#0369a1",
            "stat_label": "#64748b",
            "stat_val": "#0f172a",
            "stat_hi": "#0284c7",
            "dot": "#059669",
            "axis_text": "#64748b",
            "slab_shadow": "rgba(15, 23, 42, 0.08)",
            "base_top": "#e2e8f0",
            "base_crest": "#bae6fd",
            "base_left": "#cbd5e1",
            "base_right": "#94a3b8",
            "base_stroke": "#f8fafc",
            "halo_top": "#7dd3fc",
            "halo_left": "#38bdf8",
            "halo_right": "#0284c7",
            "halo_stroke": "#e0f2fe",
            "lvl": {
                1: ("#06b6d4", "#0891b2", "#0e7490", "#cffafe", "#ecfeff"),
                2: ("#0284c7", "#0369a1", "#075985", "#bae6fd", "#f0f9ff"),
                3: ("#10b981", "#059669", "#047857", "#a7f3d0", "#ecfdf5"),
                4: ("#9333ea", "#7e22ce", "#581c87", "#e9d5ff", "#faf5ff"),
            },
            "exciton": "#0284c7",
            "scan_beam": "#0284c7",
        }

    num_weeks = len(weeks)
    grid: dict[tuple[int, int], dict] = {}
    active_sites: list[tuple[int, int, int, int]] = []
    max_count = 0

    for w_idx, col in enumerate(weeks):
        for cell in col:
            d_idx = cell["weekday"]
            cnt = cell["count"]
            lvl = cell["level"]
            if cnt > 0 and lvl == 0:
                lvl = 1
            grid[(w_idx, d_idx)] = cell
            if cnt > 0:
                active_sites.append((w_idx, d_idx, cnt, lvl))
                if cnt > max_count:
                    max_count = cnt

    # Balanced compact vertical framing (zero cluttered floating charts)
    x0, y0 = 128.0, 128.0
    ew_x, ew_y = 15.1, 1.06
    ed_x, ed_y = -10.6, 10.5
    u_x, u_y = ew_x * 0.84, ew_y * 0.84
    v_x, v_y = ed_x * 0.82, ed_y * 0.82

    def base_xy(w: float, d: float) -> tuple[float, float]:
        return (x0 + w * ew_x + d * ed_x, y0 + w * ew_y + d * ed_y)

    def compute_halo(w: int, d: int) -> float:
        if not active_sites:
            return 0.0
        val = 0.0
        for aw, ad, _, alvl in active_sites:
            r2 = (w - aw) ** 2 + (d - ad) ** 2
            if r2 <= 7.0:
                val += (0.45 + 0.18 * alvl) * math.exp(-r2 / 2.2)
        return min(1.0, val)

    ordered_coords = sorted(grid.keys(), key=lambda wd: (wd[0] + wd[1], wd[1], wd[0]))

    prism_elems: list[str] = []
    exciton_elems: list[str] = []

    top_spires = sorted(active_sites, key=lambda item: (item[2], item[0]), reverse=True)[:12]
    top_spire_set = {(w, d) for w, d, _, _ in top_spires}

    for w, d in ordered_coords:
        cell = grid[(w, d)]
        cnt = cell["count"]
        lvl = cell["level"]
        bx, by = base_xy(w, d)
        delay = -round((w * 0.072 + d * 0.095) % 3.4, 2)

        if cnt > 0:
            norm_c = math.log1p(cnt) / math.log1p(max(max_count, 6))
            h = 20.0 + 42.0 * norm_c + 3.2 * lvl
            c_top, c_left, c_right, c_stroke, c_core = pal["lvl"].get(lvl, pal["lvl"][4])
            cls_name = "sp"
            stroke_w = "0.9"
            is_plain_sub = False
        else:
            halo = compute_halo(w, d)
            h = 5.4 + 7.5 * halo
            if halo > 0.07:
                c_top = lerp_hex(pal["base_top"], pal["halo_top"], halo)
                c_left = lerp_hex(pal["base_left"], pal["halo_left"], halo)
                c_right = lerp_hex(pal["base_right"], pal["halo_right"], halo)
                c_stroke = lerp_hex(pal["base_stroke"], pal["halo_stroke"], halo * 0.85)
                is_plain_sub = False
            else:
                c_top = pal["base_top"]
                c_left = pal["base_left"]
                c_right = pal["base_right"]
                c_stroke = pal["base_stroke"]
                is_plain_sub = True
            c_core = ""
            cls_name = "pw"
            stroke_w = "0.6"

        t0x, t0y = bx, by - h
        t1x, t1y = bx + u_x, by + u_y - h
        t2x, t2y = bx + u_x + v_x, by + u_y + v_y - h
        t3x, t3y = bx + v_x, by + v_y - h

        b1x, b1y = bx + u_x, by + u_y
        b2x, b2y = bx + u_x + v_x, by + u_y + v_y
        b3x, b3y = bx + v_x, by + v_y

        pts_left = f"{t3x:.1f},{t3y:.1f} {t2x:.1f},{t2y:.1f} {b2x:.1f},{b2y:.1f} {b3x:.1f},{b3y:.1f}"
        pts_right = f"{t2x:.1f},{t2y:.1f} {t1x:.1f},{t1y:.1f} {b1x:.1f},{b1y:.1f} {b2x:.1f},{b2y:.1f}"
        pts_top = f"{t0x:.1f},{t0y:.1f} {t1x:.1f},{t1y:.1f} {t2x:.1f},{t2y:.1f} {t3x:.1f},{t3y:.1f}"

        cap_extra = ""
        top_cls = ' class="tc"' if is_plain_sub else ""
        top_style = f' style="animation-delay:{delay:.2f}s"' if is_plain_sub else ""

        if cnt > 0:
            cx_t = 0.25 * (t0x + t1x + t2x + t3x)
            cy_t = 0.25 * (t0y + t1y + t2y + t3y)
            k_in = 0.44
            i0x, i0y = cx_t + (t0x - cx_t) * k_in, cy_t + (t0y - cy_t) * k_in
            i1x, i1y = cx_t + (t1x - cx_t) * k_in, cy_t + (t1y - cy_t) * k_in
            i2x, i2y = cx_t + (t2x - cx_t) * k_in, cy_t + (t2y - cy_t) * k_in
            i3x, i3y = cx_t + (t3x - cx_t) * k_in, cy_t + (t3y - cy_t) * k_in
            pts_inner = f"{i0x:.1f},{i0y:.1f} {i1x:.1f},{i1y:.1f} {i2x:.1f},{i2y:.1f} {i3x:.1f},{i3y:.1f}"
            cap_extra = (
                f'<polygon points="{pts_inner}" fill="{c_core}" class="gl" '
                f'style="animation-delay:{delay:.2f}s" />'
            )
            if (w, d) in top_spire_set:
                ex_delay = -round((w * 0.31 + d * 0.47) % 2.8, 2)
                exciton_elems.append(
                    f'<circle cx="{cx_t:.1f}" cy="{cy_t - 3:.1f}" r="1.9" fill="{pal["exciton"]}" '
                    f'class="ex" style="animation-delay:{ex_delay:.2f}s" />'
                )

        prism_elems.append(
            f'<g class="{cls_name}" style="animation-delay:{delay:.2f}s">'
            f'<polygon points="{pts_left}" fill="{c_left}" />'
            f'<polygon points="{pts_right}" fill="{c_right}" />'
            f'<polygon points="{pts_top}" fill="{c_top}" stroke="{c_stroke}" stroke-width="{stroke_w}" '
            f'stroke-linejoin="round"{top_cls}{top_style} />'
            f'{cap_extra}'
            f'</g>'
        )

    s0 = base_xy(-0.6, -0.4)
    s1 = base_xy(num_weeks + 0.2, -0.4)
    s2 = base_xy(num_weeks + 0.2, 6.8)
    s3 = base_xy(-0.6, 6.8)
    slab_shadow_pts = (
        f"{s0[0]:.1f},{s0[1] + 9:.1f} {s1[0]:.1f},{s1[1] + 9:.1f} "
        f"{s2[0]:.1f},{s2[1] + 11:.1f} {s3[0]:.1f},{s3[1] + 11:.1f}"
    )

    month_labels: list[str] = []
    seen_ym: set[tuple[int, int]] = set()
    last_w = -5
    for w_idx, col in enumerate(weeks):
        if not col:
            continue
        d_obj = dt.date.fromisoformat(col[0]["date"])
        ym = (d_obj.year, d_obj.month)
        if d_obj.day <= 7 and ym not in seen_ym and (w_idx - last_w) >= 3:
            seen_ym.add(ym)
            last_w = w_idx
            mx, my = base_xy(w_idx + 0.3, 7.6)
            month_labels.append(
                f'<text x="{mx:.1f}" y="{my:.1f}" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" '
                f'font-size="10.5" font-weight="500" fill="{pal["axis_text"]}">{d_obj.strftime("%b")}</text>'
            )

    day_labels = []
    for d_idx, d_name in [(0, "Sun"), (3, "Wed"), (6, "Sat")]:
        dx, dy = base_xy(-1.8, d_idx + 0.55)
        day_labels.append(
            f'<text x="{dx:.1f}" y="{dy:.1f}" text-anchor="end" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" '
            f'font-size="10" font-weight="500" fill="{pal["axis_text"]}">{d_name}</text>'
        )

    legend_items = []
    leg_x0, leg_y0 = 38.0, 282.0
    legend_colors = [pal["base_top"]] + [pal["lvl"][k][0] for k in (1, 2, 3, 4)]
    for idx, lcol in enumerate(legend_colors):
        lx = leg_x0 + 40.0 + idx * 16.0
        legend_items.append(
            f'<rect x="{lx:.1f}" y="{leg_y0 - 9:.1f}" width="11" height="11" rx="2.5" '
            f'fill="{lcol}" stroke="{pal["border"]}" stroke-width="0.7" />'
        )

    prisms_str = "\n      ".join(prism_elems)
    excitons_str = "\n      ".join(exciton_elems)
    months_str = "\n    ".join(month_labels)
    days_str = "\n    ".join(day_labels)
    legend_str = "\n    ".join(legend_items)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 304" width="100%" role="img" aria-label="3D Phonon Crystal-Lattice Contribution Field">
  <defs>
    <style>
      @keyframes phononWave {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-8.5px); }}
      }}
      @keyframes tileCrest {{
        0%, 100% {{ fill: {pal["base_top"]}; }}
        50% {{ fill: {pal["base_crest"]}; }}
      }}
      @keyframes spireMode {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-12px); }}
      }}
      @keyframes apexGlow {{
        0%, 100% {{ opacity: 0.25; }}
        50% {{ opacity: 0.85; }}
      }}
      @keyframes excitonRise {{
        0% {{ transform: translateY(0px); opacity: 0; }}
        22% {{ opacity: 0.95; }}
        100% {{ transform: translateY(-26px); opacity: 0; }}
      }}
      @keyframes laserSweep {{
        0% {{ transform: translateX(-180px); opacity: 0; }}
        12% {{ opacity: 0.65; }}
        88% {{ opacity: 0.65; }}
        100% {{ transform: translateX(920px); opacity: 0; }}
      }}
      .pw {{ animation: phononWave 3.4s ease-in-out infinite; }}
      .tc {{ animation: tileCrest 3.4s ease-in-out infinite; }}
      .sp {{ animation: spireMode 2.7s ease-in-out infinite; }}
      .gl {{ animation: apexGlow 2.7s ease-in-out infinite; }}
      .ex {{ animation: excitonRise 2.8s ease-out infinite; }}
      .sw {{ animation: laserSweep 7.2s ease-in-out infinite; }}
    </style>

    <linearGradient id="crystBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{pal["bg1"]}" />
      <stop offset="55%" stop-color="{pal["bg2"]}" />
      <stop offset="100%" stop-color="{pal["bg3"]}" />
    </linearGradient>

    <radialGradient id="slabGlowA" cx="32%" cy="56%" r="36%">
      <stop offset="0%" stop-color="{pal["glow_cyan"]}" stop-opacity="0.16" />
      <stop offset="100%" stop-color="{pal["glow_cyan"]}" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="slabGlowB" cx="76%" cy="58%" r="32%">
      <stop offset="0%" stop-color="{pal["glow_violet"]}" stop-opacity="0.11" />
      <stop offset="100%" stop-color="{pal["glow_violet"]}" stop-opacity="0" />
    </radialGradient>

    <linearGradient id="sweepGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{pal["scan_beam"]}" stop-opacity="0" />
      <stop offset="50%" stop-color="{pal["scan_beam"]}" stop-opacity="0.22" />
      <stop offset="100%" stop-color="{pal["scan_beam"]}" stop-opacity="0" />
    </linearGradient>

    <pattern id="bgLattice" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M 36 0 L 0 0 0 36" fill="none" stroke="{pal["grid"]}" stroke-opacity="{pal["grid_op"]}" stroke-width="0.9" />
    </pattern>

    <clipPath id="outerCard">
      <rect x="1" y="1" width="998" height="302" rx="16" />
    </clipPath>
  </defs>

  <g clip-path="url(#outerCard)">
    <!-- Card Background & Ambient Reciprocal Glow -->
    <rect x="1" y="1" width="998" height="302" rx="16" fill="url(#crystBg)" />
    <rect x="1" y="1" width="998" height="302" fill="url(#bgLattice)" />
    <rect x="1" y="1" width="998" height="302" fill="url(#slabGlowA)" />
    <rect x="1" y="1" width="998" height="302" fill="url(#slabGlowB)" />

    <!-- Top Scientific HUD Header -->
    <rect x="38" y="22" width="356" height="25" rx="12.5" fill="{pal["pill_bg"]}" stroke="{pal["pill_border"]}" stroke-width="1" />
    <circle cx="53" cy="34.5" r="3.5" fill="{pal["dot"]}">
      <animate attributeName="opacity" values="1;0.3;1" dur="2.2s" repeatCount="indefinite" />
    </circle>
    <text x="65" y="38.5" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="10.8" font-weight="600" letter-spacing="0.5" fill="{pal["pill_text"]}">3D PHONON CRYSTAL LATTICE · LIVE COMMIT FIELD</text>

    <!-- Top-Right Live Telemetry Readout -->
    <g transform="translate(644, 22)">
      <rect width="318" height="25" rx="12.5" fill="{pal["pill_bg"]}" stroke="{pal["border"]}" stroke-width="1" />
      <text x="159" y="16.5" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="10.6" fill="{pal["stat_label"]}">
        COMMITS <tspan fill="{pal["stat_hi"]}" font-weight="700">{total_contribs}</tspan>
        &#160;&#183;&#160; SITES <tspan fill="{pal["stat_val"]}" font-weight="600">{len(active_sites)}</tspan>
        &#160;&#183;&#160; SLAB <tspan fill="{pal["stat_val"]}" font-weight="600">{num_weeks}&#215;7</tspan>
      </text>
    </g>

    <!-- Crystallographic Slab Drop Shadow -->
    <polygon points="{slab_shadow_pts}" fill="{pal["slab_shadow"]}" />

    <!-- 3D Depth-Sorted Isometric Crystal Prisms & Phonon Modes -->
    <g>
      {prisms_str}
      {excitons_str}
    </g>

    <!-- Traveling Bragg Wavefront Sweep Overlay -->
    <polygon points="40,95 155,95 95,264 -20,264" fill="url(#sweepGrad)" class="sw" />

    <!-- Crystallographic Axes Labels -->
    {days_str}
    {months_str}

    <!-- Bottom Legend -->
    <text x="{leg_x0:.1f}" y="{leg_y0:.1f}" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="10.5" fill="{pal["axis_text"]}">Less</text>
    {legend_str}
    <text x="{leg_x0 + 125:.1f}" y="{leg_y0:.1f}" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="10.5" fill="{pal["axis_text"]}">More</text>
  </g>

  <rect x="1" y="1" width="998" height="302" rx="16" fill="none" stroke="{pal["border"]}" stroke-width="1.4" />
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default=os.environ.get("GITHUB_USER", "SuthPhy2Ai"))
    parser.add_argument("--outdir", default="dist")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        try:
            weeks, total = fetch_via_graphql(args.user, token)
            print(f"Fetched {len(weeks)} weeks ({total} total contributions) via GitHub GraphQL API.")
        except Exception as exc:
            print(f"GraphQL fetch failed ({exc}), falling back to public HTML calendar...")
            weeks, total = fetch_via_public_html(args.user)
    else:
        weeks, total = fetch_via_public_html(args.user)
        print(f"Fetched {len(weeks)} weeks ({total} total contributions) via public HTML calendar.")

    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for mode in ("dark", "light"):
        svg = generate_crystal_svg(weeks, total, mode)
        out_file = out_dir / f"crystal-lattice-{mode}.svg"
        out_file.write_text(svg, encoding="utf-8")
        print(f"Wrote {out_file} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
