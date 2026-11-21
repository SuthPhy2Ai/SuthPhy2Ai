#!/usr/bin/env python3
"""
Generate dark and light animated SVG hero banners for SuthPhy2Ai's GitHub Profile.
Pure SVG 1.1 + SMIL/CSS animations (zero <script>, zero <foreignObject>, zero external assets),
100% compatible with GitHub's camo.githubusercontent.com security proxy.
"""

from __future__ import annotations
import math
from pathlib import Path
from xml.sax.saxutils import escape


def rot_xyz(pt: tuple[float, float, float], rx_deg: float, ry_deg: float, rz_deg: float) -> tuple[float, float, float]:
    x, y, z = pt
    rx, ry, rz = map(math.radians, (rx_deg, ry_deg, rz_deg))

    # Rotate around Y
    x1 = x * math.cos(ry) + z * math.sin(ry)
    y1 = y
    z1 = -x * math.sin(ry) + z * math.cos(ry)

    # Rotate around X
    x2 = x1
    y2 = y1 * math.cos(rx) - z1 * math.sin(rx)
    z2 = y1 * math.sin(rx) + z1 * math.cos(rx)

    # Rotate around Z
    x3 = x2 * math.cos(rz) - y2 * math.sin(rz)
    y3 = x2 * math.sin(rz) + y2 * math.cos(rz)
    z3 = z2
    return (x3, y3, z3)


def build_orbital_paths(cx: float, cy: float, scale: float, tilt_deg: float = -24.0) -> tuple[str, str]:
    """Compute analytical d_z2 spherical harmonic lobes (3*cos^2(theta) - 1) split into + and - phase paths."""
    tilt = math.radians(tilt_deg)
    pos_pts_top = []
    pos_pts_bot = []
    neg_pts_left = []
    neg_pts_right = []

    # In polar coords around axis `tilt`, 3*cos^2(t) - 1 = 0 at cos(t) = +/- 1/sqrt(3) => t0 ~ 54.7356 deg
    t0 = math.acos(1.0 / math.sqrt(3.0))

    def sample_lobe(t_start: float, t_end: float, steps: int = 48) -> str:
        pts = [(cx, cy)]
        for i in range(steps + 1):
            t = t_start + (t_end - t_start) * (i / steps)
            amp = abs(3.0 * (math.cos(t) ** 2) - 1.0) / 2.0  # normalized to [0, 1]
            r = scale * amp
            ang = t + tilt - math.pi / 2.0
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)
            pts.append((px, py))
        pts.append((cx, cy))
        return "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"

    pos_top = sample_lobe(-t0, t0)
    pos_bot = sample_lobe(math.pi - t0, math.pi + t0)
    neg_right = sample_lobe(t0, math.pi - t0)
    neg_left = sample_lobe(math.pi + t0, 2.0 * math.pi - t0)
    return f"{pos_top} {pos_bot}", f"{neg_right} {neg_left}"


def build_crystal_svg(cx: float, cy: float, cell_half: float, theme: dict) -> str:
    """Render depth-sorted 3D perovskite ABO3 unit cell + BO6 coordination octahedron + E(3) message pulses."""
    rx, ry, rz = 21.0, -34.0, 7.0

    def proj(p: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = rot_xyz(p, rx, ry, rz)
        return (cx + x * cell_half, cy - y * cell_half, z)

    # 8 A-site corners at (+/-1, +/-1, +/-1)
    corners_3d = [(sx, sy, sz) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0) for sz in (-1.0, 1.0)]
    corners_2d = {c: proj(c) for c in corners_3d}

    # 12 cube edges
    cube_edges = []
    for i, c1 in enumerate(corners_3d):
        for c2 in corners_3d[i + 1 :]:
            diff = sum(abs(a - b) > 1e-6 for a, b in zip(c1, c2))
            if diff == 1:
                p1, p2 = corners_2d[c1], corners_2d[c2]
                z_mid = 0.5 * (p1[2] + p2[2])
                cube_edges.append((z_mid, p1, p2))
    cube_edges.sort(key=lambda item: item[0])

    # 6 face-centered O-sites forming BO6 octahedron
    oct_3d = [
        (1.0, 0.0, 0.0),
        (-1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, -1.0),
    ]
    oct_2d = [proj(p) for p in oct_3d]
    center_2d = proj((0.0, 0.0, 0.0))

    # 8 triangular facets of octahedron: (+/-x, +/-y, +/-z)
    oct_map = {p: proj(p) for p in oct_3d}
    facets = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                p_x = oct_map[(sx, 0.0, 0.0)]
                p_y = oct_map[(0.0, sy, 0.0)]
                p_z = oct_map[(0.0, 0.0, sz)]
                z_avg = (p_x[2] + p_y[2] + p_z[2]) / 3.0
                facets.append((z_avg, p_x, p_y, p_z))
    facets.sort(key=lambda f: f[0])

    lines: list[str] = []

    # 1. Back half of unit cell wireframe
    for z_mid, p1, p2 in cube_edges[:6]:
        lines.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{theme["cell_back"]}" stroke-width="1.1" stroke-dasharray="3 3" />'
        )

    # 2. Back A-site corner atoms (z < 0)
    for c, (px, py, pz) in sorted(corners_2d.items(), key=lambda kv: kv[1][2]):
        if pz < 0:
            lines.append(
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="3.6" fill="{theme["atom_a_back"]}" '
                f'stroke="{theme["atom_stroke"]}" stroke-width="0.8" opacity="0.72" />'
            )

    # 3. Back facets of BO6 octahedron
    for z_avg, p1, p2, p3 in facets[:4]:
        pts_str = f"{p1[0]:.2f},{p1[1]:.2f} {p2[0]:.2f},{p2[1]:.2f} {p3[0]:.2f},{p3[1]:.2f}"
        lines.append(
            f'<polygon points="{pts_str}" fill="{theme["oct_fill_back"]}" '
            f'stroke="{theme["oct_edge"]}" stroke-width="0.9" stroke-linejoin="round" />'
        )

    # 4. B-O coordination bonds + animated E(3) message-passing pulses
    for idx, (ox, oy, oz) in enumerate(oct_2d):
        lines.append(
            f'<line x1="{center_2d[0]:.2f}" y1="{center_2d[1]:.2f}" x2="{ox:.2f}" y2="{oy:.2f}" '
            f'stroke="{theme["bond"]}" stroke-width="1.5" stroke-opacity="0.85" />'
        )
        delay = f"{idx * 0.45:.2f}s"
        lines.append(
            f'<circle r="2.4" fill="{theme["pulse"]}">'
            f'<animate attributeName="cx" values="{center_2d[0]:.2f};{ox:.2f};{center_2d[0]:.2f}" '
            f'dur="2.8s" begin="{delay}" repeatCount="indefinite" />'
            f'<animate attributeName="cy" values="{center_2d[1]:.2f};{oy:.2f};{center_2d[1]:.2f}" '
            f'dur="2.8s" begin="{delay}" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="0.95;0.35;0.95" '
            f'dur="2.8s" begin="{delay}" repeatCount="indefinite" />'
            f'</circle>'
        )

    # 5. Central B-site transition metal atom (with subtle breathing halo)
    lines.append(
        f'<circle cx="{center_2d[0]:.2f}" cy="{center_2d[1]:.2f}" r="11" fill="{theme["atom_b_glow"]}" opacity="0.35">'
        f'<animate attributeName="r" values="9;14;9" dur="3.2s" repeatCount="indefinite" />'
        f'<animate attributeName="opacity" values="0.45;0.15;0.45" dur="3.2s" repeatCount="indefinite" />'
        f'</circle>'
    )
    lines.append(
        f'<circle cx="{center_2d[0]:.2f}" cy="{center_2d[1]:.2f}" r="6.5" fill="url(#gradAtomB)" '
        f'stroke="{theme["atom_b_ring"]}" stroke-width="1.2" />'
    )

    # 6. Front facets of BO6 octahedron
    for z_avg, p1, p2, p3 in facets[4:]:
        pts_str = f"{p1[0]:.2f},{p1[1]:.2f} {p2[0]:.2f},{p2[1]:.2f} {p3[0]:.2f},{p3[1]:.2f}"
        lines.append(
            f'<polygon points="{pts_str}" fill="{theme["oct_fill_front"]}" '
            f'stroke="{theme["oct_edge_front"]}" stroke-width="1.15" stroke-linejoin="round" />'
        )

    # 7. All 6 O-site coordination atoms sorted by depth
    for ox, oy, oz in sorted(oct_2d, key=lambda p: p[2]):
        r_o = 4.6 if oz >= 0 else 3.9
        op_o = 0.98 if oz >= 0 else 0.80
        lines.append(
            f'<circle cx="{ox:.2f}" cy="{oy:.2f}" r="{r_o}" fill="url(#gradAtomO)" '
            f'stroke="{theme["atom_stroke"]}" stroke-width="0.9" opacity="{op_o}" />'
        )

    # 8. Front half of unit cell wireframe
    for z_mid, p1, p2 in cube_edges[6:]:
        lines.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{theme["cell_front"]}" stroke-width="1.35" />'
        )

    # 9. Front A-site corner atoms (z >= 0)
    for c, (px, py, pz) in sorted(corners_2d.items(), key=lambda kv: kv[1][2]):
        if pz >= 0:
            lines.append(
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4.3" fill="url(#gradAtomA)" '
                f'stroke="{theme["atom_stroke"]}" stroke-width="0.95" />'
            )

    return "\n    ".join(lines)


def build_typewriter_svg(x_text: float, y_text: float, theme: dict) -> tuple[str, str]:
    """
    Build pure-SVG 3-line cycling typewriter animation using <clipPath> + SMIL <animate>.
    Total cycle = 15s (5s per line).
    Line 0 starts fully typed at t=0 (holds 0..2.7s, erases 2.7..3.4s, re-types 13.5..15.0s)
    so static thumbnail renderers at t=0 show full text + cursor while live SMIL loops seamlessly!
    """
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
        # Line 0: full at t=0..2.7s, erase by 3.35s, stay 0 until 13.5s, type 13.5..15.0s -> full at 15s (=0s)
        (
            ["0", "0.1800", "0.2233", "0.9000", "0.9001", "1"],
            lambda w: [f"{w:.1f}", f"{w:.1f}", "0", "0", "0", f"{w:.1f}"],
            ["0.95", "0.95", "0", "0", "0.95", "0.95"],
        ),
        # Line 1: type 3.5..5.0s (0.2333..0.3333), hold 5.0..7.7s (..0.5133), erase by 8.35s (0.5567)
        (
            ["0", "0.2332", "0.2333", "0.3333", "0.5133", "0.5567", "1"],
            lambda w: ["0", "0", "0", f"{w:.1f}", f"{w:.1f}", "0", "0"],
            ["0", "0", "0.95", "0.95", "0.95", "0", "0"],
        ),
        # Line 2: type 8.5..10.0s (0.5667..0.6667), hold 10.0..12.7s (..0.8467), erase by 13.35s (0.8900)
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

        # Synced cursor for active window
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
            "bg1": "#080d1a",
            "bg2": "#0f172a",
            "bg3": "#131c33",
            "border": "#1e293b",
            "grid": "#38bdf8",
            "grid_op": "0.055",
            "glow1": "#0ea5e9",
            "glow1_op": "0.18",
            "glow2": "#8b5cf6",
            "glow2_op": "0.14",
            "pill_bg": "#111c33",
            "pill_border": "#1e3a5f",
            "pill_text": "#7dd3fc",
            "dot": "#34d399",
            "name": "#f8fafc",
            "handle": "#38bdf8",
            "subtitle": "#cbd5e1",
            "term_bg": "#09101f",
            "term_border": "#1e293b",
            "prompt": "#34d399",
            "term_text": "#e2e8f0",
            "cursor": "#38bdf8",
            "chip_bg": "#111b2e",
            "chip_border": "#233554",
            "chip_text": "#94a3b8",
            "chip_accent": "#38bdf8",
            "ring_outer": "#38bdf8",
            "ring_inner": "#a78bfa",
            "lobe_pos_1": "#38bdf8",
            "lobe_pos_2": "#0284c7",
            "lobe_neg_1": "#c084fc",
            "lobe_neg_2": "#7c3aed",
            "cell_back": "#475569",
            "cell_front": "#64748b",
            "oct_fill_back": "rgba(14, 165, 233, 0.10)",
            "oct_fill_front": "rgba(56, 189, 248, 0.17)",
            "oct_edge": "rgba(56, 189, 248, 0.35)",
            "oct_edge_front": "rgba(125, 211, 252, 0.65)",
            "bond": "#38bdf8",
            "pulse": "#fde047",
            "atom_b_1": "#e0f2fe",
            "atom_b_2": "#0284c7",
            "atom_b_glow": "#38bdf8",
            "atom_b_ring": "#bae6fd",
            "atom_o_1": "#ddd6fe",
            "atom_o_2": "#7c3aed",
            "atom_a_1": "#cbd5e1",
            "atom_a_2": "#475569",
            "atom_a_back": "#64748b",
            "atom_stroke": "#0f172a",
            "formula": "#94a3b8",
            "formula_hi": "#7dd3fc",
        }
    else:
        theme = {
            "bg1": "#f8fafc",
            "bg2": "#f1f5f9",
            "bg3": "#eef2ff",
            "border": "#cbd5e1",
            "grid": "#0284c7",
            "grid_op": "0.065",
            "glow1": "#0284c7",
            "glow1_op": "0.11",
            "glow2": "#7c3aed",
            "glow2_op": "0.09",
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
            "ring_outer": "#0284c7",
            "ring_inner": "#7c3aed",
            "lobe_pos_1": "#0ea5e9",
            "lobe_pos_2": "#0369a1",
            "lobe_neg_1": "#a855f7",
            "lobe_neg_2": "#6d28d9",
            "cell_back": "#94a3b8",
            "cell_front": "#475569",
            "oct_fill_back": "rgba(2, 132, 199, 0.09)",
            "oct_fill_front": "rgba(14, 165, 233, 0.16)",
            "oct_edge": "rgba(2, 132, 199, 0.35)",
            "oct_edge_front": "rgba(3, 105, 161, 0.65)",
            "bond": "#0284c7",
            "pulse": "#f59e0b",
            "atom_b_1": "#bae6fd",
            "atom_b_2": "#0369a1",
            "atom_b_glow": "#0ea5e9",
            "atom_b_ring": "#0284c7",
            "atom_o_1": "#ede9fe",
            "atom_o_2": "#6d28d9",
            "atom_a_1": "#f1f5f9",
            "atom_a_2": "#475569",
            "atom_a_back": "#94a3b8",
            "atom_stroke": "#ffffff",
            "formula": "#475569",
            "formula_hi": "#0369a1",
        }

    cx, cy = 812.0, 138.0
    pos_lobe_path, neg_lobe_path = build_orbital_paths(cx, cy, scale=96.0, tilt_deg=-24.0)
    crystal_markup = build_crystal_svg(cx, cy, cell_half=45.0, theme=theme)
    type_defs, type_nodes = build_typewriter_svg(x_text=74.0, y_text=192.0, theme=theme)

    # Bragg spots around reciprocal ring r = 108
    bragg_nodes = []
    for k in range(6):
        ang = math.radians(k * 60.0 + 15.0)
        bx = cx + 108.0 * math.cos(ang)
        by = cy + 108.0 * math.sin(ang)
        r_b = 2.6 if k % 2 == 0 else 2.0
        bragg_nodes.append(
            f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{r_b}" fill="{theme["ring_outer"]}" opacity="0.75" />'
        )
    bragg_str = "\n      ".join(bragg_nodes)

    # Research chips
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

    <radialGradient id="ambientCyan" cx="81%" cy="48%" r="26%">
      <stop offset="0%" stop-color="{theme["glow1"]}" stop-opacity="{theme["glow1_op"]}" />
      <stop offset="100%" stop-color="{theme["glow1"]}" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="ambientViolet" cx="76%" cy="54%" r="22%">
      <stop offset="0%" stop-color="{theme["glow2"]}" stop-opacity="{theme["glow2_op"]}" />
      <stop offset="100%" stop-color="{theme["glow2"]}" stop-opacity="0" />
    </radialGradient>

    <pattern id="crystGrid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M 36 0 L 0 0 0 36" fill="none" stroke="{theme["grid"]}" stroke-opacity="{theme["grid_op"]}" stroke-width="0.9" />
    </pattern>

    <linearGradient id="lobePosGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{theme["lobe_pos_1"]}" stop-opacity="0.34" />
      <stop offset="100%" stop-color="{theme["lobe_pos_2"]}" stop-opacity="0.10" />
    </linearGradient>

    <linearGradient id="lobeNegGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{theme["lobe_neg_1"]}" stop-opacity="0.30" />
      <stop offset="100%" stop-color="{theme["lobe_neg_2"]}" stop-opacity="0.08" />
    </linearGradient>

    <radialGradient id="gradAtomB" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="{theme["atom_b_1"]}" />
      <stop offset="100%" stop-color="{theme["atom_b_2"]}" />
    </radialGradient>

    <radialGradient id="gradAtomO" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="{theme["atom_o_1"]}" />
      <stop offset="100%" stop-color="{theme["atom_o_2"]}" />
    </radialGradient>

    <radialGradient id="gradAtomA" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="{theme["atom_a_1"]}" />
      <stop offset="100%" stop-color="{theme["atom_a_2"]}" />
    </radialGradient>

    <clipPath id="cardClip">
      <rect x="1" y="1" width="998" height="282" rx="16" />
    </clipPath>

    {type_defs}
  </defs>

  <g clip-path="url(#cardClip)">
    <!-- Background & crystallographic lattice grid -->
    <rect x="1" y="1" width="998" height="282" rx="16" fill="url(#bgGrad)" />
    <rect x="1" y="1" width="998" height="282" fill="url(#crystGrid)" />
    <rect x="1" y="1" width="998" height="282" fill="url(#ambientCyan)" />
    <rect x="1" y="1" width="998" height="282" fill="url(#ambientViolet)" />

    <!-- Top affiliation pill -->
    <rect x="46" y="34" width="358" height="26" rx="13" fill="{theme["pill_bg"]}" stroke="{theme["pill_border"]}" stroke-width="1" />
    <circle cx="62" cy="47" r="6" fill="{theme["dot"]}" opacity="0.25">
      <animate attributeName="r" values="4;8;4" dur="2.4s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.45;0.08;0.45" dur="2.4s" repeatCount="indefinite" />
    </circle>
    <circle cx="62" cy="47" r="3.6" fill="{theme["dot"]}" />
    <text x="75" y="51" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="11" font-weight="600" letter-spacing="0.6" fill="{theme["pill_text"]}">SHANGHAI UNIVERSITY · MATERIALS INFORMATICS</text>

    <!-- Name & GitHub handle -->
    <text x="46" y="108" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="40" font-weight="800" letter-spacing="-0.6" fill="{theme["name"]}">Tianhao Su</text>
    <text x="272" y="106" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="15.5" font-weight="600" fill="{theme["handle"]}">@SuthPhy2Ai</text>

    <!-- Core identity subtitle -->
    <text x="46" y="140" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="16" font-weight="500" fill="{theme["subtitle"]}">Physics × Deep Learning · First-Principles &amp; Autonomous Materials Discovery</text>

    <!-- Terminal Typewriter Bar -->
    <rect x="46" y="166" width="582" height="40" rx="8" fill="{theme["term_bg"]}" stroke="{theme["term_border"]}" stroke-width="1.1" />
    <text x="58" y="191.5" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="13.5" font-weight="700" fill="{theme["prompt"]}">&gt;</text>
    {type_nodes}

    <!-- Research Pillar Chips -->
    {chips_str}

    <!-- Right Visual: Reciprocal Diffraction Rings + Spherical Harmonics + 3D ABO3 Crystal -->
    <g>
      <!-- Rotating outer reciprocal lattice ring -->
      <g>
        <circle cx="{cx:.1f}" cy="{cy:.1f}" r="108" fill="none" stroke="{theme["ring_outer"]}" stroke-opacity="0.28" stroke-width="1.1" stroke-dasharray="3 7" />
        {bragg_str}
        <animateTransform attributeName="transform" type="rotate" from="0 {cx:.1f} {cy:.1f}" to="360 {cx:.1f} {cy:.1f}" dur="48s" repeatCount="indefinite" />
      </g>

      <!-- Counter-rotating inner harmonic ring -->
      <g>
        <circle cx="{cx:.1f}" cy="{cy:.1f}" r="82" fill="none" stroke="{theme["ring_inner"]}" stroke-opacity="0.25" stroke-width="1.0" stroke-dasharray="2 5" />
        <animateTransform attributeName="transform" type="rotate" from="360 {cx:.1f} {cy:.1f}" to="0 {cx:.1f} {cy:.1f}" dur="34s" repeatCount="indefinite" />
      </g>

      <!-- Analytical d_z2 spherical harmonic lobes (Y_2^0) -->
      <path d="{pos_lobe_path}" fill="url(#lobePosGrad)" stroke="{theme["lobe_pos_1"]}" stroke-opacity="0.45" stroke-width="1.0">
        <animate attributeName="opacity" values="0.72;1.0;0.72" dur="4.4s" repeatCount="indefinite" />
      </path>
      <path d="{neg_lobe_path}" fill="url(#lobeNegGrad)" stroke="{theme["lobe_neg_1"]}" stroke-opacity="0.40" stroke-width="1.0">
        <animate attributeName="opacity" values="0.95;0.65;0.95" dur="4.4s" repeatCount="indefinite" />
      </path>

      <!-- 3D Perovskite ABO3 Unit Cell & E(3) Message Passing -->
      {crystal_markup}
    </g>

    <!-- Bottom-right equivariant operator caption -->
    <text x="{cx:.1f}" y="266" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="500" fill="{theme["formula"]}">
      <tspan fill="{theme["formula_hi"]}" font-weight="700">E(3)</tspan> &#183; <tspan font-style="italic">Y</tspan><tspan dy="-4.2" font-size="8.5" font-style="italic">l,m</tspan><tspan dy="4.2">(</tspan><tspan font-style="italic">r&#770;</tspan><tspan dy="3" font-size="8.5" font-style="italic">ij</tspan><tspan dy="-3">) &#8855; </tspan><tspan font-style="italic">h</tspan><tspan dy="3" font-size="8.5" font-style="italic">j</tspan><tspan dy="-3"> &#8594; &#961;(</tspan><tspan font-style="italic">r</tspan><tspan>)</tspan>
    </text>
  </g>

  <!-- Crisp outer card border -->
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
