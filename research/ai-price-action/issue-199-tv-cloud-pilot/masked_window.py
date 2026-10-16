"""Render one anonymized, future-masked daily candlestick window as SVG (Issue #199, Phase B).

Input: a local OHLC(V) CSV the user is licensed to use (columns: date,open,high,low,close[,volume]),
sorted ascending. Raw prices never leave the machine: the chart rebases to close[t0]=100 and drops
dates/symbol, and the output belongs in the git-ignored `out/` folder.

Only bars [cut-bars, cut) are drawn, so nothing at or after `cut` is visible (no lookahead).

    python masked_window.py data/x.csv --cut 1800 --bars 200 --out out/w01.svg
"""
import argparse
import csv
import hashlib


def load(path):
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    bars = []
    for r in rows:
        o, h, l, c = (float(r[k]) for k in ("open", "high", "low", "close"))
        if not (l <= min(o, c) and h >= max(o, c)):
            raise ValueError(f"OHLC inconsistent on {r['date']}")
        bars.append((o, h, l, c))
    return bars


def render(win, width=1000, height=500, pad=20):
    base = win[0][3]
    win = [tuple(100 * v / base for v in b) for b in win]
    lo = min(b[2] for b in win)
    hi = max(b[1] for b in win)
    y = lambda v: pad + (hi - v) / (hi - lo or 1) * (height - 2 * pad)
    step = (width - 2 * pad) / len(win)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             f'<rect width="{width}" height="{height}" fill="white"/>']
    for i, (o, h, l, c) in enumerate(win):
        x = pad + (i + 0.5) * step
        col = "#1a7f37" if c >= o else "#cf222e"
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(h):.1f}" y2="{y(l):.1f}" stroke="{col}"/>')
        top, bot = y(max(o, c)), y(min(o, c))
        parts.append(f'<rect x="{x - step * 0.35:.1f}" y="{top:.1f}" width="{step * 0.7:.1f}" '
                     f'height="{max(bot - top, 0.5):.1f}" fill="{col}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--cut", type=int, required=True, help="index of first hidden bar")
    ap.add_argument("--bars", type=int, default=200, help="150-250")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not 150 <= a.bars <= 250:
        raise SystemExit("bars must be in [150, 250]")
    bars = load(a.csv)
    if not a.bars <= a.cut <= len(bars):
        raise SystemExit(f"cut must be in [{a.bars}, {len(bars)}]")
    svg = render(bars[a.cut - a.bars:a.cut])
    with open(a.out, "w") as f:
        f.write(svg)
    print(a.out, hashlib.sha256(svg.encode()).hexdigest()[:12])


if __name__ == "__main__":
    main()
