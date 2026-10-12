"""Deterministic chart rendering for the PTM v0.2 engineering review.

Pillow only (no matplotlib in this environment).  Charts are a *visual audit of
the indicator trajectory*, not trading evidence.  Every chart is a pure
function of the fixture and the frozen configuration, so re-running the study
reproduces byte-stable PNGs.
"""

from __future__ import annotations

import os
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

BG = (255, 255, 255)
GRID = (226, 232, 240)
AXIS = (100, 116, 139)
TEXT = (30, 41, 59)
PRICE = (15, 23, 42)
INNER = (191, 219, 254)
OUTER = (219, 234, 254)
REF_HIGH = (220, 38, 38)
REF_LOW = (22, 163, 74)
NOVELTY = (37, 99, 235)
ACCEPT = (124, 58, 237)
OCCUPANCY = (234, 88, 12)
PROBE = (16, 185, 129)
CLAIM = (220, 38, 38)
STALL = (148, 163, 184)

W, H = 1180, 980
LEFT, RIGHT = 78, 1150
TOP = 92


def _font(size: int = 12) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


class Panel:
    def __init__(self, top: int, height: int, ymin: float, ymax: float,
                 label: str, fmt: str = "{:.2f}") -> None:
        self.top = top
        self.height = height
        self.ymin = ymin
        self.ymax = ymax
        self.label = label
        self.fmt = fmt

    def y(self, v: float) -> float:
        if self.ymax == self.ymin:
            return self.top + self.height / 2.0
        frac = (v - self.ymin) / (self.ymax - self.ymin)
        frac = max(0.0, min(1.0, frac))
        return self.top + self.height * (1.0 - frac)


def _x(i: int, i0: int, i1: int) -> float:
    if i1 <= i0:
        return LEFT
    return LEFT + (RIGHT - LEFT) * (i - i0) / float(i1 - i0)


def _line(draw: ImageDraw.ImageDraw, pts: Sequence[tuple[float, float]],
          color, width: int = 2) -> None:
    if len(pts) >= 2:
        draw.line(list(pts), fill=color, width=width, joint="curve")


def _text(draw, xy, s, color=TEXT, size=12, anchor="la"):
    draw.text(xy, s, fill=color, font=_font(size), anchor=anchor)


def _draw_panel_frame(draw, panel: Panel, i0: int, i1: int, step: int = 20) -> None:
    draw.rectangle([LEFT, panel.top, RIGHT, panel.top + panel.height], outline=AXIS)
    _text(draw, (LEFT + 8, panel.top + 5), panel.label, color=TEXT, size=12)
    for k in range(3):
        v = panel.ymin + (panel.ymax - panel.ymin) * k / 2.0
        y = panel.y(v)
        draw.line([(LEFT, y), (RIGHT, y)], fill=GRID, width=1)
        _text(draw, (LEFT - 8, y), panel.fmt.format(v), color=AXIS, size=11, anchor="rm")
    for i in range(i0, i1 + 1, step):
        x = _x(i, i0, i1)
        draw.line([(x, panel.top), (x, panel.top + panel.height)], fill=GRID, width=1)
        _text(draw, (x, panel.top + panel.height + 6), str(i), color=AXIS, size=10,
              anchor="ma")


def _legend(draw, x: float, y: float) -> None:
    items = [
        (PRICE, "price"),
        ((148, 163, 184), "pre-probe context"),
        ((22, 163, 74), "probe anchor"),
        (INNER, "inner band"),
        (OUTER, "outer band"),
        (NOVELTY, "novelty"),
        (ACCEPT, "acceptance"),
        (OCCUPANCY, "occupancy"),
        (CLAIM, "claim"),
        ((148, 163, 184), "stalled"),
        (REF_HIGH, "frozen ref high"),
        (REF_LOW, "frozen ref low"),
    ]
    cx = x
    for colour, label in items:
        draw.rectangle([cx, y + 3, cx + 10, y + 13], fill=colour)
        _text(draw, (cx + 14, y), label, color=TEXT, size=10)
        cx += 18 + int(6.2 * len(label))
        if cx > RIGHT - 160:
            cx = x
            y += 16
    return


def render_scenario_chart(
    observations: Sequence,
    bars: Sequence,
    reference,
    title: str,
    path: str,
    context_bars: int = 20,
) -> str:
    """Render one 3-panel audit chart: price+bands, novelty+acceptance, occupancy."""
    obs = list(observations)
    anchor = obs[0].anchor_index
    i0 = max(0, anchor - context_bars)
    i1 = obs[-1].bar_index
    validity = obs[0].validity
    w = obs[0].w

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    _text(draw, (LEFT, 14), title, color=TEXT, size=15)
    _text(draw, (LEFT, 36),
          f"anchor bar {anchor} | direction {obs[0].direction:+d} | "
          f"w={w} | validity {validity} | closed-bar values, actionable next bar",
          color=AXIS, size=11)
    _legend(draw, LEFT, 58)

    usable = [o for o in obs if o.w is not None]
    if not usable:
        _text(draw, (LEFT, 120), "NO USABLE REFERENCE -- fail closed, no numbers",
              color=CLAIM, size=16)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        img.save(path)
        return path

    ctx = [bars[i] for i in range(i0, min(anchor, len(bars)))]
    closes = [o.close for o in obs] + [b.close for b in ctx]
    lo = min(closes)
    hi = max(closes)
    lo = min(lo, min(o.outer_low for o in usable))
    hi = max(hi, max(o.outer_high for o in usable))
    pad = max((hi - lo) * 0.08, 1e-9)

    p_price = Panel(TOP, 330, lo - pad, hi + pad, "PRICE  (fuzzy inner/outer band)")

    # Outer band ribbon (light) then inner band ribbon (darker).
    outer_hi = [(_x(o.bar_index, i0, i1), p_price.y(o.outer_high)) for o in usable]
    outer_lo = [(_x(o.bar_index, i0, i1), p_price.y(o.outer_low)) for o in reversed(usable)]
    draw.polygon(outer_hi + outer_lo, fill=OUTER)
    inner_hi = [(_x(o.bar_index, i0, i1), p_price.y(o.inner_high)) for o in usable]
    inner_lo = [(_x(o.bar_index, i0, i1), p_price.y(o.inner_low)) for o in reversed(usable)]
    draw.polygon(inner_hi + inner_lo, fill=INNER)

    # Frozen reference envelope: context only, never a required gate.
    _draw_panel_frame(draw, p_price, i0, i1)
    if reference is not None and reference.max_high is not None:
        for level, colour in ((reference.max_high, REF_HIGH),
                              (reference.min_low, REF_LOW)):
            if p_price.ymin <= level <= p_price.ymax:
                y = p_price.y(level)
                for x in range(int(LEFT), int(RIGHT), 12):
                    draw.line([(x, y), (x + 6, y)], fill=colour, width=2)
    if ctx:
        _line(draw, [(_x(i0 + k, i0, i1), p_price.y(b.close)) for k, b in enumerate(ctx)],
              (148, 163, 184), 2)
    _line(draw, [(_x(o.bar_index, i0, i1), p_price.y(o.close)) for o in obs], PRICE, 2)

    x_probe = _x(anchor, i0, i1)
    draw.line([(x_probe, p_price.top), (x_probe, p_price.top + p_price.height)],
              fill=PROBE, width=2)

    p_nov = Panel(TOP + 400, 210, 0.0, 1.05, "NOVELTY 1/(1+R)  and  3-close acceptance trace")
    _draw_panel_frame(draw, p_nov, i0, i1)
    _line(draw, [(_x(o.bar_index, i0, i1), p_nov.y(o.novelty)) for o in usable],
          NOVELTY, 2)
    _line(draw, [(_x(o.bar_index, i0, i1), p_nov.y(o.acceptance_trace)) for o in usable],
          ACCEPT, 2)
    for o in obs:
        if o.is_new_territory_claim:
            x = _x(o.bar_index, i0, i1)
            y = p_nov.y(o.novelty)
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=CLAIM)

    p_occ = Panel(TOP + 650, 170, 0.0, 1.05, "OCCUPANCY  share of frozen reference bars touching the inner band")
    _draw_panel_frame(draw, p_occ, i0, i1)
    for o in usable:
        x = _x(o.bar_index, i0, i1)
        y0 = p_occ.y(0.0)
        y1 = p_occ.y(o.occupancy)
        draw.line([(x, y1), (x, y0)], fill=OCCUPANCY, width=3)
        if o.stall_flag:
            draw.line([(x, p_occ.top), (x, p_occ.top + 8)], fill=STALL, width=2)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    return path


COMPARE_COLOURS = [
    (37, 99, 235),    # box
    (22, 163, 74),    # true trend
    (220, 38, 38),    # fake breakout
    (124, 58, 237),   # healthy retest
    (234, 88, 12),
    (13, 148, 136),
]


def render_comparison_chart(series, title: str, path: str) -> str:
    """Overlay novelty trajectories (bars since probe) for side-by-side reading."""
    img = Image.new("RGB", (W, 650), BG)
    draw = ImageDraw.Draw(img)
    _text(draw, (LEFT, 14), title, color=TEXT, size=15)
    _text(draw, (LEFT, 40), "same frozen configuration; each curve is one synthetic "
                            "path, offset to its own probe anchor", color=AXIS, size=11)

    x0, x1 = 0, max(o.bar_index - o.anchor_index for _, obs in series for o in obs)
    panel_nov = Panel(TOP + 20, 190, 0.0, 1.05, "NOVELTY by bars since probe anchor")
    panel_acc = Panel(TOP + 300, 170, 0.0, 1.05, "ACCEPTANCE TRACE by bars since probe anchor")
    for panel in (panel_nov, panel_acc):
        _draw_panel_frame(draw, panel, x0, x1, step=max(1, (x1 - x0) // 12 or 1))

    for k, (label, obs) in enumerate(series):
        colour = COMPARE_COLOURS[k % len(COMPARE_COLOURS)]
        pts_n = [(_x(o.bar_index - o.anchor_index, x0, x1), panel_nov.y(o.novelty))
                 for o in obs if o.novelty is not None]
        _line(draw, pts_n, colour, 2)
        pts_a = [(_x(o.bar_index - o.anchor_index, x0, x1), panel_acc.y(o.acceptance_trace))
                 for o in obs if o.acceptance_trace is not None]
        _line(draw, pts_a, colour, 2)
        _text(draw, (LEFT + 10 + 230 * (k % 4), 68 + 16 * (k // 4)),
              f"-- {label}", color=colour, size=12)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    return path
