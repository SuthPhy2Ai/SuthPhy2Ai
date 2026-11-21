#!/usr/bin/env python3
"""
Generate dark and light animated SVG hero banners for SuthPhy2Ai's GitHub Profile.
Right-side visual is a direct pure-SVG port of DeePAW's OrbitalBackground.tsx:
- 3 breathing radial-glow PAW nuclei (Cyan #0ea5e9, Indigo #6366f1, Rose #ec4899) with pinpoint cores
- Zero wireframe orbit rings: ~34 pinpoint electrons swarming freely along softened-Coulomb
  precessing rosettes & inter-nuclear exchange paths with short, delicate motion-blur wisps
- Strong-field PAW core physics inside halo radius: high-frequency quantum jitter particles,
  orthogonal glitch flashes, and flickering radial quantum-entanglement filaments.
"""

from __future__ import annotations
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape


def sample_closed_curve(fn, n_pts: int = 96) -> str:
    pts = [fn(i / n_pts) for i in range(n_pts)]
    return f"M {pts[0][0]:.2f},{pts[0][1]:.2f} " + " ".join(f"L {x:.2f},{y:.2f}" for x, y in pts[1:]) + " Z"


def precessing_coulomb_path(
    cx: float,
    cy: float,
    r_mean: float,
    ecc: float,
    lobes_num: int,
    lobes_den: int,
    tilt_deg: float,
    ccw: bool = False,
) -> str:
    """
    Exact closed periodic rosette orbit in DeePAW's softened potential V(r) = -k / sqrt(r^2 + a^2),
    closing after `lobes_den` revolutions with `lobes_num` radial oscillations.
    """
    tilt = math.radians(tilt_deg)
    ct, st = math.cos(tilt), math.sin(tilt)
    total_ang = 2.0 * math.pi * lobes_den
    n_pts = 72 * lobes_den

    def pt(u: float) -> tuple[float, float]:
        theta = (-total_ang * u) if ccw else (total_ang * u)
        r = r_mean * (1.0 - ecc * math.cos((lobes_num / lobes_den) * theta))
        # Slight 3D perspective compression along minor axis
        ex = r * math.cos(theta)
        ey = r * 0.72 * math.sin(theta)
        return (cx + ex * ct - ey * st, cy + ex * st + ey * ct)

    return sample_closed_curve(pt, n_pts=n_pts)


def exchange_orbit_path(
    p1: tuple[float, float],
    p2: tuple[float, float],
    waist: float,
    ccw: bool = False,
) -> str:
    """Smooth two-center valence electron exchange trajectory hopping between two PAW nuclei."""
    mx, my = 0.5 * (p1[0] + p2[0]), 0.5 * (p1[1] + p2[1])
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    half_d = 0.5 * math.hypot(dx, dy)
    ux, uy = dx / (2.0 * half_d), dy / (2.0 * half_d)
    nx, ny = -uy, ux
    a = half_d * 1.28

    def pt(u: float) -> tuple[float, float]:
        t = (-2.0 * math.pi * u) if ccw else (2.0 * math.pi * u)
        denom = 1.0 + 0.52 * (math.sin(t) ** 2)
        lx = a * math.cos(t) / denom
        ly = waist * math.sin(t) * math.cos(t) / denom + 0.22 * waist * math.sin(t)
        return (mx + lx * ux + ly * nx, my + lx * uy + ly * ny)

    return sample_closed_curve(pt, n_pts=100)


def render_electron_particle(
    path_d: str,
    color: str,
    dot_size: float,
    dur_s: float,
    phase_frac: float,
    wisp_len: float = 34.0,
    wisp_op: float = 0.34,
) -> str:
    """
    Render a single pinpoint electron + delicate short motion-blur wisp (matching Canvas rgba fade in DeePAW),
    with ZERO visible orbit wireframe ring.
    """
    s0 = (phase_frac % 1.0) * 1000.0

    def anim_dash(seg_len: float) -> str:
        off_start = seg_len - s0
        off_end = off_start - 1000.0
        return (
            f'stroke-dasharray="{seg_len:.2f} {1000.0 - seg_len:.2f}" '
            f'stroke-dashoffset="{off_start:.2f}">'
            f'<animate attributeName="stroke-dashoffset" from="{off_start:.2f}" to="{off_end:.2f}" '
            f'dur="{dur_s:.2f}s" repeatCount="indefinite" />'
        )

    mid_len = wisp_len * 0.36
    return (
        f'<path d="{path_d}" pathLength="1000" fill="none" stroke="{color}" stroke-opacity="{wisp_op * 0.55:.2f}" '
        f'stroke-width="{dot_size * 0.52:.2f}" stroke-linecap="round" {anim_dash(wisp_len)}</path>\n      '
        f'<path d="{path_d}" pathLength="1000" fill="none" stroke="{color}" stroke-opacity="{wisp_op:.2f}" '
        f'stroke-width="{dot_size * 0.78:.2f}" stroke-linecap="round" {anim_dash(mid_len)}</path>\n      '
        f'<path d="{path_d}" pathLength="1000" fill="none" stroke="{color}" stroke-opacity="0.96" '
        f'stroke-width="{dot_size:.2f}" stroke-linecap="round" {anim_dash(0.5)}</path>'
    )


def build_deepaw_orbital_svg(mode: str) -> str:
    """Port DeePAW's OrbitalBackground.tsx (3 breathing nuclei + swarming electrons + core jitter/glitch/entanglement)."""
    rng = random.Random(20261121)
    is_dark = mode == "dark"

    # 3 PAW atomic centers scaled to the right-side viewport (x = 640..985, y = 12..272)
    n0 = (806.0, 144.0)  # Center primary cyan PAW atom (r_halo = 86)
    n1 = (926.0, 64.0)   # Upper-right indigo atom (r_halo = 48)
    n2 = (706.0, 222.0)  # Lower-left rose-pink atom (r_halo = 52)

    palette = ["#38bdf8", "#818cf8", "#22d3ee"] if is_dark else ["#0284c7", "#4f46e5", "#0891b2"]
    core_spark_col = "#ffffff" if is_dark else "#0369a1"
    glitch_col = "#ffffff" if is_dark else "#0284c7"
    entangle_col = "#38bdf8" if is_dark else "#0284c7"
    core_dot_fill = "#f0f9ff" if is_dark else "#ffffff"
    wisp_op = 0.42 if is_dark else 0.46

    elems: list[str] = []

    # 1. Three Breathing & Gently Drifting PAW Nuclei (exact port of OrbitalBackground.tsx lines 416-456)
    nuclei_cfg = [
        ("pawHaloCyan", n0, 88.0, 4.4, "0s", "#0ea5e9", 4.6),
        ("pawHaloIndigo", n1, 48.0, 3.3, "-1.2s", "#6366f1", 3.2),
        ("pawHaloRose", n2, 54.0, 3.8, "-2.4s", "#ec4899", 3.5),
    ]
    for grad_id, (nx, ny), r_base, dur_b, begin_b, glow_c, r_pin in nuclei_cfg:
        r_lo, r_hi = r_base * 0.90, r_base * 1.11
        elems.append(
            f'<g>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0,0; 4,-3; -3,2.5; 0,0" dur="{dur_b * 1.7:.1f}s" begin="{begin_b}" repeatCount="indefinite" />'
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{r_base:.1f}" fill="url(#{grad_id})">'
            f'<animate attributeName="r" values="{r_lo:.1f};{r_hi:.1f};{r_lo:.1f}" dur="{dur_b:.1f}s" begin="{begin_b}" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="0.72;1.0;0.72" dur="{dur_b:.1f}s" begin="{begin_b}" repeatCount="indefinite" />'
            f'</circle>'
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{r_pin * 2.6:.1f}" fill="{glow_c}" opacity="{0.42 if is_dark else 0.30}">'
            f'<animate attributeName="r" values="{r_pin * 2.0:.1f};{r_pin * 3.3:.1f};{r_pin * 2.0:.1f}" dur="{dur_b:.1f}s" begin="{begin_b}" repeatCount="indefinite" />'
            f'</circle>'
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{r_pin:.1f}" fill="{core_dot_fill}" />'
            f'</g>'
        )

    # 2. Outer & Mid-Field Swarming Valence Electrons (NO wireframe tracks, pinpoint dots + subtle motion wisps)
    # 20 electrons around Primary Nucleus n0
    for i in range(20):
        r_m = 46.0 + (i / 19.0) * 76.0 + rng.uniform(-4.0, 4.0)
        ecc = rng.uniform(0.12, 0.34)
        l_num, l_den = [(1, 1), (3, 2), (2, 1), (4, 3)][i % 4]
        tilt = (i * 37.0 + rng.uniform(-10.0, 10.0)) % 180.0 - 90.0
        ccw = (i % 2 == 1)
        col = palette[i % len(palette)]
        dot_sz = rng.uniform(2.1, 3.6)
        # Kepler-like scaling: inner electrons orbit faster than outer electrons
        dur_orb = (2.2 + 0.028 * r_m) * l_den
        ph = (i * 0.173 + rng.uniform(0.0, 0.08)) % 1.0
        wisp = max(18.0, 42.0 / l_den)
        pd = precessing_coulomb_path(n0[0], n0[1], r_m, ecc, l_num, l_den, tilt, ccw=ccw)
        elems.append(render_electron_particle(pd, col, dot_sz, dur_orb, ph, wisp_len=wisp, wisp_op=wisp_op))

    # 6 electrons around Indigo Nucleus n1 & 6 around Rose Nucleus n2
    for sat_idx, (snx, sny) in enumerate([n1, n2]):
        for j in range(6):
            r_m = 20.0 + j * 5.8
            ecc = rng.uniform(0.10, 0.28)
            tilt = j * 31.0 - 60.0
            ccw = ((j + sat_idx) % 2 == 0)
            col = palette[(j + sat_idx) % len(palette)]
            dot_sz = rng.uniform(1.9, 3.0)
            dur_orb = 1.65 + 0.03 * r_m
            ph = (j * 0.21 + sat_idx * 0.13) % 1.0
            pd = precessing_coulomb_path(snx, sny, r_m, ecc, 1, 1, tilt, ccw=ccw)
            elems.append(render_electron_particle(pd, col, dot_sz, dur_orb, ph, wisp_len=44.0, wisp_op=wisp_op))

    # 4 Dynamic Exchange Electrons hopping between nuclei (Feature 2 of OrbitalBackground.tsx)
    exchanges = [
        (n0, n1, 28.0, False, palette[0], 3.8, 0.14),
        (n0, n1, 20.0, True, palette[1], 4.3, 0.64),
        (n0, n2, 30.0, True, palette[2], 4.1, 0.37),
        (n0, n2, 22.0, False, "#f472b6" if is_dark else "#db2777", 4.6, 0.83),
    ]
    for pa, pb, wst, ccw, col, dur_x, ph_x in exchanges:
        pd = exchange_orbit_path(pa, pb, waist=wst, ccw=ccw)
        elems.append(render_electron_particle(pd, col, 3.2, dur_x, ph_x, wisp_len=36.0, wisp_op=wisp_op * 1.1))

    # 3. Strong-Field Inner-Core Jittering Electrons + Quantum Entanglement Lines + Glitch Crosshairs
    # (Exact port of OrbitalBackground.tsx lines 496-559: `shouldJitter = inGlowRadius`)
    for k in range(7):
        base_ang = k * (2.0 * math.pi / 7.0)
        r_core = 14.0 + (k % 3) * 8.5
        n_kf = 16
        xs, ys, line_ops = [], [], []
        for step in range(n_kf):
            ang = base_ang + 2.0 * math.pi * (step / n_kf)
            # Exponential strong-field jitter shake inside r_PAW
            jx = rng.uniform(-6.5, 6.5)
            jy = rng.uniform(-6.5, 6.5)
            px = n0[0] + r_core * math.cos(ang) + jx
            py = n0[1] + r_core * math.sin(ang) + jy
            xs.append(f"{px:.1f}")
            ys.append(f"{py:.1f}")
            line_ops.append("0.62" if (step + k * 2) % 6 == 0 else "0")
        xs.append(xs[0])
        ys.append(ys[0])
        line_ops.append(line_ops[0])

        dur_j = 1.05 + k * 0.14
        xs_str = ";".join(xs)
        ys_str = ";".join(ys)
        ops_str = ";".join(line_ops)
        col_j = core_spark_col if k % 2 == 0 else palette[k % len(palette)]

        # Flickering quantum entanglement line connecting nucleus center to jittering core electron
        elems.append(
            f'<line x1="{n0[0]:.1f}" y1="{n0[1]:.1f}" x2="{xs[0]}" y2="{ys[0]}" '
            f'stroke="{entangle_col}" stroke-width="0.85" opacity="0">'
            f'<animate attributeName="x2" values="{xs_str}" dur="{dur_j:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="y2" values="{ys_str}" dur="{dur_j:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="{ops_str}" dur="{dur_j:.2f}s" repeatCount="indefinite" />'
            f'</line>'
        )
        # Jittering core electron particle
        elems.append(
            f'<circle cx="{xs[0]}" cy="{ys[0]}" r="{1.9 if k % 2 == 0 else 1.6}" fill="{col_j}">'
            f'<animate attributeName="cx" values="{xs_str}" dur="{dur_j:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="cy" values="{ys_str}" dur="{dur_j:.2f}s" repeatCount="indefinite" />'
            f'</circle>'
        )

    # High-field orthogonal glitch streaks inside central PAW core (OrbitalBackground.tsx lines 515-527)
    for g_idx in range(6):
        ang = rng.uniform(0, 2.0 * math.pi)
        rad = rng.uniform(8.0, 28.0)
        gx = n0[0] + rad * math.cos(ang)
        gy = n0[1] + rad * math.sin(ang)
        horiz = (g_idx % 2 == 0)
        gw = rng.uniform(12.0, 24.0) if horiz else 1.1
        gh = 1.1 if horiz else rng.uniform(12.0, 22.0)
        dur_g = 1.5 + g_idx * 0.31
        beg_g = f"-{g_idx * 0.42:.2f}s"
        elems.append(
            f'<rect x="{gx - gw / 2:.1f}" y="{gy - gh / 2:.1f}" width="{gw:.1f}" height="{gh:.1f}" '
            f'fill="{glitch_col}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;0.75;0;0;0;0" dur="{dur_g:.2f}s" begin="{beg_g}" repeatCount="indefinite" />'
            f'</rect>'
        )

    return "\n    ".join(elems)


def build_typewriter_svg(x_text: float, y_text: float, theme: dict) -> tuple[str, str]:
    taglines = [
        "Teaching E(3)-equivariant GNNs crystallographic symmetry",
        "Sub-angstrom PAW charge density & electrostatic landscapes",
        "Inverse crystal design & 2D diffraction reconstruction",
    ]
    char_px = 8.25
    total_dur = 15.0

    defs_out = []
    nodes_out = []

    schedules = [
        (
            ["0", "0.1800", "0.2233", "0.9000", "0.9001", "1"],
            lambda w: [f"{w:.1f}", f"{w:.1f}", "0", "0", "0", f"{w:.1f}"],
            ["0.95", "0.95", "0", "0", "0.95", "0.95"],
        ),
        (
            ["0", "0.2332", "0.2333", "0.3333", "0.5133", "0.5567", "1"],
            lambda w: ["0", "0", "0", f"{w:.1f}", f"{w:.1f}", "0", "0"],
            ["0", "0", "0.95", "0.95", "0.95", "0", "0"],
        ),
        (
            ["0", "0.5666", "0.5667", "0.6667", "0.8467", "0.8900", "1"],
            lambda w: ["0", "0", "0", f"{w:.1f}", f"{w:.1f}", "0", "0"],
            ["0", "0", "0.95", "0.95", "0.95", "0", "0"],
        ),
    ]

    for idx, line in enumerate(taglines):
        w = round(len(line) * char_px + 8.0, 1)
        key_times, w_fn, values_op = schedules[idx]
        values_w = w_fn(w)

        kt_str = ";".join(key_times)
        vw_str = ";".join(values_w)
        vop_str = ";".join(values_op)
        vx_cursor = ";".join(f"{x_text + float(v):.1f}" for v in values_w)

        clip_id = f"typeClip{idx}"
        init_w = f"{w:.1f}" if idx == 0 else "0"
        init_x = f"{x_text + w:.1f}" if idx == 0 else f"{x_text:.1f}"
        init_op = "0.95" if idx == 0 else "0"
        defs_out.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{x_text:.1f}" y="{y_text - 16:.1f}" width="{init_w}" height="24">'
            f'<animate attributeName="width" dur="{total_dur:.0f}s" repeatCount="indefinite" '
            f'keyTimes="{kt_str}" values="{vw_str}" />'
            f'</rect>'
            f'</clipPath>'
        )

        nodes_out.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="{x_text:.1f}" y="{y_text:.1f}" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" '
            f'font-size="13.2" font-weight="500" fill="{theme["term_text"]}">{escape(line)}</text>'
            f'</g>'
        )

        nodes_out.append(
            f'<rect x="{init_x}" y="{y_text - 12.5:.1f}" width="7.5" height="15" rx="1.5" fill="{theme["cursor"]}" opacity="{init_op}">'
            f'<animate attributeName="x" dur="{total_dur:.0f}s" repeatCount="indefinite" '
            f'keyTimes="{kt_str}" values="{vx_cursor}" />'
            f'<animate attributeName="opacity" dur="{total_dur:.0f}s" repeatCount="indefinite" '
            f'keyTimes="{kt_str}" values="{vop_str}" />'
            f'</rect>'
        )

    return "\n    ".join(defs_out), "\n    ".join(nodes_out)


def generate_svg(mode: str) -> str:
    if mode == "dark":
        theme = {
            "bg1": "#020617",
            "bg2": "#071024",
            "bg3": "#0c1730",
            "border": "#1e293b",
            "grid": "#38bdf8",
            "grid_op": "0.04",
            "pill_bg": "#0f1b33",
            "pill_border": "#1e3a5f",
            "pill_text": "#7dd3fc",
            "dot": "#34d399",
            "name": "#f8fafc",
            "handle": "#38bdf8",
            "subtitle": "#cbd5e1",
            "term_bg": "#060d1d",
            "term_border": "#1e293b",
            "prompt": "#34d399",
            "term_text": "#e2e8f0",
            "cursor": "#38bdf8",
            "chip_bg": "#0d182c",
            "chip_border": "#1e3252",
            "chip_text": "#94a3b8",
            "chip_accent": "#38bdf8",
            "halo_cyan_0": "#0ea5e9",
            "halo_cyan_op0": "0.72",
            "halo_cyan_op1": "0.24",
            "halo_ind_0": "#6366f1",
            "halo_ind_op0": "0.65",
            "halo_ind_op1": "0.20",
            "halo_rose_0": "#ec4899",
            "halo_rose_op0": "0.58",
            "halo_rose_op1": "0.18",
        }
    else:
        theme = {
            "bg1": "#f8fafc",
            "bg2": "#f1f5f9",
            "bg3": "#e8f0fe",
            "border": "#cbd5e1",
            "grid": "#0284c7",
            "grid_op": "0.05",
            "pill_bg": "#e0f2fe",
            "pill_border": "#bae6fd",
            "pill_text": "#0369a1",
            "dot": "#059669",
            "name": "#0f172a",
            "handle": "#0284c7",
            "subtitle": "#334155",
            "term_bg": "#ffffff",
            "term_border": "#cbd5e1",
            "prompt": "#059669",
            "term_text": "#1e293b",
            "cursor": "#0284c7",
            "chip_bg": "#ffffff",
            "chip_border": "#cbd5e1",
            "chip_text": "#475569",
            "chip_accent": "#0284c7",
            "halo_cyan_0": "#0ea5e9",
            "halo_cyan_op0": "0.48",
            "halo_cyan_op1": "0.16",
            "halo_ind_0": "#6366f1",
            "halo_ind_op0": "0.42",
            "halo_ind_op1": "0.14",
            "halo_rose_0": "#ec4899",
            "halo_rose_op0": "0.38",
            "halo_rose_op1": "0.12",
        }

    orbital_markup = build_deepaw_orbital_svg(mode)
    type_defs, type_nodes = build_typewriter_svg(x_text=74.0, y_text=192.0, theme=theme)

    chips = [
        ("E(3)-Equivariant GNN", 158),
        ("PAW Charge Density", 150),
        ("Crystal Generation", 142),
        ("XRD Reconstruction", 150),
    ]
    chip_svg = []
    cur_x = 46
    for label, width in chips:
        chip_svg.append(
            f'<g transform="translate({cur_x}, 224)">'
            f'<rect width="{width}" height="27" rx="6" fill="{theme["chip_bg"]}" stroke="{theme["chip_border"]}" stroke-width="1" />'
            f'<circle cx="12.5" cy="13.5" r="2.5" fill="{theme["chip_accent"]}" />'
            f'<text x="21" y="17.5" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif" '
            f'font-size="11.4" font-weight="500" fill="{theme["chip_text"]}">{escape(label)}</text>'
            f'</g>'
        )
        cur_x += width + 7
    chips_str = "\n  ".join(chip_svg)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 284" width="100%" role="img" aria-label="Tianhao Su — Physics x Deep Learning Research">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{theme["bg1"]}" />
      <stop offset="55%" stop-color="{theme["bg2"]}" />
      <stop offset="100%" stop-color="{theme["bg3"]}" />
    </linearGradient>

    <radialGradient id="pawHaloCyan" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{theme["halo_cyan_0"]}" stop-opacity="{theme["halo_cyan_op0"]}" />
      <stop offset="40%" stop-color="{theme["halo_cyan_0"]}" stop-opacity="{theme["halo_cyan_op1"]}" />
      <stop offset="100%" stop-color="{theme["halo_cyan_0"]}" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="pawHaloIndigo" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{theme["halo_ind_0"]}" stop-opacity="{theme["halo_ind_op0"]}" />
      <stop offset="40%" stop-color="{theme["halo_ind_0"]}" stop-opacity="{theme["halo_ind_op1"]}" />
      <stop offset="100%" stop-color="{theme["halo_ind_0"]}" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="pawHaloRose" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{theme["halo_rose_0"]}" stop-opacity="{theme["halo_rose_op0"]}" />
      <stop offset="40%" stop-color="{theme["halo_rose_0"]}" stop-opacity="{theme["halo_rose_op1"]}" />
      <stop offset="100%" stop-color="{theme["halo_rose_0"]}" stop-opacity="0" />
    </radialGradient>

    <pattern id="crystGrid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M 36 0 L 0 0 0 36" fill="none" stroke="{theme["grid"]}" stroke-opacity="{theme["grid_op"]}" stroke-width="0.9" />
    </pattern>

    <clipPath id="cardClip">
      <rect x="1" y="1" width="998" height="282" rx="16" />
    </clipPath>

    {type_defs}
  </defs>

  <g clip-path="url(#cardClip)">
    <rect x="1" y="1" width="998" height="282" rx="16" fill="url(#bgGrad)" />
    <rect x="1" y="1" width="998" height="282" fill="url(#crystGrid)" />

    <!-- Right Visual: DeePAW Multi-Nucleus Electron Swarm & PAW Strong-Field Core -->
    <g>
      {orbital_markup}
    </g>

    <!-- Left Typography & Terminal -->
    <rect x="46" y="34" width="358" height="26" rx="13" fill="{theme["pill_bg"]}" stroke="{theme["pill_border"]}" stroke-width="1" />
    <circle cx="62" cy="47" r="6" fill="{theme["dot"]}" opacity="0.25">
      <animate attributeName="r" values="4;8;4" dur="2.4s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.45;0.08;0.45" dur="2.4s" repeatCount="indefinite" />
    </circle>
    <circle cx="62" cy="47" r="3.6" fill="{theme["dot"]}" />
    <text x="75" y="51" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="11" font-weight="600" letter-spacing="0.6" fill="{theme["pill_text"]}">SHANGHAI UNIVERSITY · MATERIALS INFORMATICS</text>

    <text x="46" y="108" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="40" font-weight="800" letter-spacing="-0.6" fill="{theme["name"]}">Tianhao Su</text>
    <text x="272" y="106" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="15.5" font-weight="600" fill="{theme["handle"]}">@SuthPhy2Ai</text>

    <text x="46" y="140" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="16" font-weight="500" fill="{theme["subtitle"]}">Physics × Deep Learning · First-Principles &amp; Autonomous Materials Discovery</text>

    <rect x="46" y="166" width="582" height="40" rx="8" fill="{theme["term_bg"]}" stroke="{theme["term_border"]}" stroke-width="1.1" />
    <text x="58" y="191.5" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="13.5" font-weight="700" fill="{theme["prompt"]}">&gt;</text>
    {type_nodes}

    {chips_str}
  </g>

  <rect x="1" y="1" width="998" height="282" rx="16" fill="none" stroke="{theme["border"]}" stroke-width="1.4" />
</svg>
'''


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    for mode in ("dark", "light"):
        svg_text = generate_svg(mode)
        out_path = assets / f"banner-{mode}.svg"
        out_path.write_text(svg_text, encoding="utf-8")
        print(f"Wrote {out_path} ({len(svg_text)} bytes)")


if __name__ == "__main__":
    main()
