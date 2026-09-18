#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MARKER = 'ISSUE76|schema=1'
TREND = {2: 'Markup', 5: 'Markdown'}
ERAS = (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2026", 2020, 2026))
EPS = 1e-12

# +1 means higher is hypothesized to indicate better responsiveness.
# -1 means lower is hypothesized to indicate better responsiveness.
FEATURES = {}
for k in (5, 10):
    info = f'E{k}'
    FEATURES.update({
        f'e{k}_cum_atr': (+1, info, 'baseline_progress'),
        f'e{k}_dir_eff': (+1, info, 'baseline_efficiency'),
        f'e{k}_favorable_day_share': (+1, info, 'consistency'),
        f'e{k}_new_high_rate': (+1, info, 'extension'),
        f'e{k}_mae_atr': (-1, info, 'adverse_excursion'),
        f'e{k}_max_pullback_atr': (-1, info, 'pullback'),
        f'e{k}_activity_ratio20': (+1, info, 'activity_expansion'),
        f'e{k}_bars_to_half_atr': (-1, info, 'response_speed'),
    })


def parse_marker(text: str):
    p = text.find(MARKER)
    if p < 0:
        return None
    out = {}
    for tok in text[p:].strip().split('|'):
        if '=' in tok:
            k, v = tok.split('=', 1)
            out[k] = v
    return out


def read_events(paths):
    dedup = {}
    for path in paths:
        with Path(path).open(encoding='utf-8-sig', newline='') as fh:
            for row in csv.reader(fh):
                fields = None
                for cell in row:
                    fields = parse_marker(cell)
                    if fields:
                        break
                if not fields:
                    continue
                rec = {
                    'ticker': fields['ticker'],
                    'repr': fields['repr'],
                    'event_time': int(fields['event_time']),
                    'event_bar': int(fields['event_bar']),
                    'stage': int(fields['stage']),
                    'fresh': int(fields['fresh']),
                    'scale': float(fields['scale']),
                    'move1': float(fields['move1']),
                }
                dedup[(rec['ticker'], rec['event_time'], rec['event_bar'])] = rec
    return sorted(dedup.values(), key=lambda r: (r['ticker'], r['event_bar']))


def episodes(events):
    by = defaultdict(list)
    for e in events:
        by[e['ticker']].append(e)
    out = []
    for ticker, rows in by.items():
        rows.sort(key=lambda r: r['event_bar'])
        i = 0
        episode_id = 0
        while i < len(rows):
            r = rows[i]
            stage = r['stage']
            if stage in TREND and r['fresh'] == 1:
                j = i + 1
                while (
                    j < len(rows)
                    and rows[j]['stage'] == stage
                    and rows[j]['event_bar'] == rows[j - 1]['event_bar'] + 1
                ):
                    j += 1
                if j < len(rows):
                    out.append((ticker, stage, episode_id, rows[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return out


def denom_entry(row):
    return row['scale'] * (100.0 if row['repr'] == 'YIELD_LEVEL' else 1.0)


def steps_entry_atr(stage, rows):
    den = denom_entry(rows[0])
    direction = 1.0 if stage == 2 else -1.0
    return [r['move1'] / den * direction for r in rows]


def trailing_rows(index_by_bar, entry_bar, h):
    rows = []
    for bar in range(entry_bar - h, entry_bar):
        r = index_by_bar.get(bar)
        if r is None:
            return None
        rows.append(r)
    return rows


def era(ms):
    year = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).year
    for name, a, b in ERAS:
        if a <= year <= b:
            return name
    return 'other'


def mean(xs):
    vals = [x for x in xs if isinstance(x, (int, float)) and math.isfinite(x)]
    return statistics.fmean(vals) if vals else math.nan


def median(xs):
    vals = [x for x in xs if isinstance(x, (int, float)) and math.isfinite(x)]
    return statistics.median(vals) if vals else math.nan


def auc(pos, neg):
    if not pos or not neg:
        return math.nan
    wins = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def percentile_ranks(vals):
    n = len(vals)
    if not n:
        return []
    order = sorted(range(n), key=lambda i: vals[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i + 1
        while j < n and vals[order[j]] == vals[order[i]]:
            j += 1
        average_rank = (i + j - 1) / 2
        pct = average_rank / (n - 1) if n > 1 else 0.5
        for x in range(i, j):
            ranks[order[x]] = pct
        i = j
    return ranks


def early_responsiveness(steps, k, pre20_mean_abs):
    if len(steps) < k:
        return None
    s = steps[:k]
    cumulative = 0.0
    peak = 0.0
    trough = 0.0
    max_pullback = 0.0
    new_highs = 0
    favorable_days = 0
    bars_to_half = k + 1

    for i, step in enumerate(s, start=1):
        if step > 0:
            favorable_days += 1
        cumulative += step
        trough = min(trough, cumulative)
        if cumulative > peak + EPS:
            peak = cumulative
            new_highs += 1
        max_pullback = max(max_pullback, peak - cumulative)
        if bars_to_half == k + 1 and cumulative >= 0.5:
            bars_to_half = i

    path = sum(abs(x) for x in s)
    dir_eff = cumulative / path if path > 0 else math.nan
    activity = path / k
    activity_ratio20 = activity / pre20_mean_abs if pre20_mean_abs and pre20_mean_abs > 0 else math.nan

    return {
        'cum_atr': cumulative,
        'dir_eff': dir_eff,
        'favorable_day_share': favorable_days / k,
        'new_high_rate': new_highs / k,
        'mae_atr': max(0.0, -trough),
        'max_pullback_atr': max_pullback,
        'activity_ratio20': activity_ratio20,
        'bars_to_half_atr': float(bars_to_half),
    }


def build_episode_rows(events, eps):
    by = defaultdict(dict)
    for r in events:
        by[r['ticker']][r['event_bar']] = r

    out = []
    for ticker, stage, episode_id, rows in eps:
        entry = rows[0]
        den = denom_entry(entry)
        steps = steps_entry_atr(stage, rows)

        cumulative = 0.0
        mfe = 0.0
        for x in steps:
            cumulative += x
            mfe = max(mfe, cumulative)

        if mfe < 4:
            label = 'Failed'
        elif mfe >= 8:
            label = 'Large'
        else:
            label = 'Middle'

        pre20 = trailing_rows(by[ticker], entry['event_bar'], 20)
        if pre20:
            pre20_mean_abs = mean([abs(r['move1']) / den for r in pre20])
        else:
            pre20_mean_abs = math.nan

        rec = {
            'ticker': ticker,
            'stage': TREND[stage],
            'episode_id': episode_id,
            'entry_time': entry['event_time'],
            'entry_bar': entry['event_bar'],
            'era': era(entry['event_time']),
            'bars': len(steps),
            'mfe': mfe,
            'label': label,
        }

        for k in (5, 10):
            vals = early_responsiveness(steps, k, pre20_mean_abs)
            names = (
                'cum_atr', 'dir_eff', 'favorable_day_share', 'new_high_rate',
                'mae_atr', 'max_pullback_atr', 'activity_ratio20', 'bars_to_half_atr'
            )
            if vals is None:
                for name in names:
                    rec[f'e{k}_{name}'] = math.nan
            else:
                for name in names:
                    rec[f'e{k}_{name}'] = vals[name]
        out.append(rec)
    return out


def separation_rows(ep_rows):
    out = []
    scopes = [('all', ep_rows)] + [
        (name, [r for r in ep_rows if r['era'] == name]) for name, _, _ in ERAS
    ]
    for feature, (orientation, info, family) in FEATURES.items():
        for scope, subset in scopes:
            markets = []
            for ticker in sorted(set(r['ticker'] for r in subset)):
                g = [
                    r for r in subset
                    if r['ticker'] == ticker
                    and r['label'] in ('Large', 'Failed')
                    and math.isfinite(r.get(feature, math.nan))
                ]
                pos = [orientation * r[feature] for r in g if r['label'] == 'Large']
                neg = [orientation * r[feature] for r in g if r['label'] == 'Failed']
                if len(pos) >= 3 and len(neg) >= 3:
                    markets.append({
                        'ticker': ticker,
                        'auc': auc(pos, neg),
                        'large_n': len(pos),
                        'failed_n': len(neg),
                        'large_median': median([r[feature] for r in g if r['label'] == 'Large']),
                        'failed_median': median([r[feature] for r in g if r['label'] == 'Failed']),
                    })
            if markets:
                out.append({
                    'feature': feature,
                    'information_set': info,
                    'family': family,
                    'orientation': orientation,
                    'scope': scope,
                    'markets': len(markets),
                    'large_n': sum(m['large_n'] for m in markets),
                    'failed_n': sum(m['failed_n'] for m in markets),
                    'eq_market_mean_auc': mean([m['auc'] for m in markets]),
                    'eq_market_median_auc': median([m['auc'] for m in markets]),
                    'markets_auc_gt_0_5': sum(m['auc'] > 0.5 for m in markets),
                    'eq_market_large_median': mean([m['large_median'] for m in markets]),
                    'eq_market_failed_median': mean([m['failed_median'] for m in markets]),
                })
    return out


def direction_rows(ep_rows):
    out = []
    for feature, (orientation, info, family) in FEATURES.items():
        for stage in ('Markup', 'Markdown'):
            subset = [r for r in ep_rows if r['stage'] == stage]
            markets = []
            for ticker in sorted(set(r['ticker'] for r in subset)):
                g = [
                    r for r in subset
                    if r['ticker'] == ticker
                    and r['label'] in ('Large', 'Failed')
                    and math.isfinite(r.get(feature, math.nan))
                ]
                pos = [orientation * r[feature] for r in g if r['label'] == 'Large']
                neg = [orientation * r[feature] for r in g if r['label'] == 'Failed']
                if len(pos) >= 3 and len(neg) >= 3:
                    markets.append(auc(pos, neg))
            if markets:
                out.append({
                    'feature': feature,
                    'information_set': info,
                    'family': family,
                    'stage': stage,
                    'markets': len(markets),
                    'eq_market_mean_auc': mean(markets),
                    'markets_auc_gt_0_5': sum(x > 0.5 for x in markets),
                })
    return out


def quintile_rows(ep_rows):
    out = []
    for feature, (orientation, info, family) in FEATURES.items():
        assignments = []
        for ticker in sorted(set(r['ticker'] for r in ep_rows)):
            g = [r for r in ep_rows if math.isfinite(r.get(feature, math.nan)) and r['ticker'] == ticker]
            if len(g) < 20:
                continue
            scores = [orientation * r[feature] for r in g]
            ranks = percentile_ranks(scores)
            for r, pct in zip(g, ranks):
                q = min(5, int(pct * 5) + 1)
                assignments.append((ticker, q, r))

        for q in range(1, 6):
            per_market = []
            for ticker in sorted(set(x[0] for x in assignments)):
                gg = [r for t, qq, r in assignments if t == ticker and qq == q]
                if not gg:
                    continue
                per_market.append({
                    'large_share': mean([1.0 if r['label'] == 'Large' else 0.0 for r in gg]),
                    'failed_share': mean([1.0 if r['label'] == 'Failed' else 0.0 for r in gg]),
                    'n': len(gg),
                })
            if per_market:
                out.append({
                    'feature': feature,
                    'information_set': info,
                    'family': family,
                    'quality_quintile': q,
                    'markets': len(per_market),
                    'episodes': sum(x['n'] for x in per_market),
                    'eq_market_large_share': mean([x['large_share'] for x in per_market]),
                    'eq_market_failed_share': mean([x['failed_share'] for x in per_market]),
                })
    return out


def conditional_rows(ep_rows):
    out = []
    for feature, (orientation, info, family) in FEATURES.items():
        if family == 'baseline_progress':
            continue
        k = 5 if info == 'E5' else 10
        baseline = f'e{k}_cum_atr'
        scopes = [('all', ep_rows)] + [
            (name, [r for r in ep_rows if r['era'] == name]) for name, _, _ in ERAS
        ]
        for scope, subset in scopes:
            market_rows = []
            for ticker in sorted(set(r['ticker'] for r in subset)):
                g = [
                    r for r in subset
                    if r['ticker'] == ticker
                    and r['label'] in ('Large', 'Failed')
                    and math.isfinite(r.get(feature, math.nan))
                    and math.isfinite(r.get(baseline, math.nan))
                ]
                if len(g) < 12:
                    continue
                ranks = percentile_ranks([r[baseline] for r in g])
                band_aucs = []
                valid_bands = 0
                for band in (1, 2, 3):
                    band_rows = []
                    for r, pct in zip(g, ranks):
                        b = min(3, int(pct * 3) + 1)
                        if b == band:
                            band_rows.append(r)
                    pos = [orientation * r[feature] for r in band_rows if r['label'] == 'Large']
                    neg = [orientation * r[feature] for r in band_rows if r['label'] == 'Failed']
                    if len(pos) >= 3 and len(neg) >= 3:
                        band_aucs.append(auc(pos, neg))
                        valid_bands += 1
                if valid_bands >= 2:
                    market_rows.append({
                        'ticker': ticker,
                        'conditional_auc': mean(band_aucs),
                        'valid_bands': valid_bands,
                    })
            if market_rows:
                out.append({
                    'feature': feature,
                    'information_set': info,
                    'family': family,
                    'scope': scope,
                    'markets': len(market_rows),
                    'eq_market_mean_conditional_auc': mean([x['conditional_auc'] for x in market_rows]),
                    'eq_market_median_conditional_auc': median([x['conditional_auc'] for x in market_rows]),
                    'markets_conditional_auc_gt_0_5': sum(x['conditional_auc'] > 0.5 for x in market_rows),
                    'mean_valid_bands': mean([x['valid_bands'] for x in market_rows]),
                })
    return out


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inputs', nargs='+')
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    events = read_events(args.inputs)
    eps = episodes(events)
    if len(events) != 68118:
        raise SystemExit(f'event count drift: {len(events)}')
    if len(eps) != 1624:
        raise SystemExit(f'episode count drift: {len(eps)}')

    rows = build_episode_rows(events, eps)
    separation = separation_rows(rows)
    quintiles = quintile_rows(rows)
    directions = direction_rows(rows)
    conditional = conditional_rows(rows)

    out = Path(args.output_dir)
    write_csv(out / 'issue81-market-responsiveness-episodes.csv', rows)
    write_csv(out / 'issue81-market-responsiveness-separation.csv', separation)
    write_csv(out / 'issue81-market-responsiveness-quintiles.csv', quintiles)
    write_csv(out / 'issue81-market-responsiveness-direction.csv', directions)
    write_csv(out / 'issue81-market-responsiveness-conditional.csv', conditional)

    print(
        'events', len(events),
        'episodes', len(eps),
        'large', sum(r['label'] == 'Large' for r in rows),
        'failed', sum(r['label'] == 'Failed' for r in rows),
        'middle', sum(r['label'] == 'Middle' for r in rows),
    )
    print('\nUNCONDITIONAL ALL-YEARS')
    for r in sorted(
        [x for x in separation if x['scope'] == 'all'],
        key=lambda x: (x['information_set'], -x['eq_market_mean_auc'])
    ):
        print(
            f"{r['feature']:34s} {r['information_set']} "
            f"auc={r['eq_market_mean_auc']:.3f} "
            f"gt50={r['markets_auc_gt_0_5']}/{r['markets']}"
        )
    print('\nCONDITIONAL ON CUMULATIVE-PROOF TERCILES')
    for r in sorted(
        [x for x in conditional if x['scope'] == 'all'],
        key=lambda x: (x['information_set'], -x['eq_market_mean_conditional_auc'])
    ):
        print(
            f"{r['feature']:34s} {r['information_set']} "
            f"cond_auc={r['eq_market_mean_conditional_auc']:.3f} "
            f"gt50={r['markets_conditional_auc_gt_0_5']}/{r['markets']}"
        )


if __name__ == '__main__':
    main()
