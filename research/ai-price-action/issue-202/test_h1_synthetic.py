"""Issue #202: frozen T1/T2/T3 signal parity on synthetic bars ONLY.

Run: python -m unittest -v test_h1_synthetic.py
No market-data calls, outcome computation, strategy returns or optimization.
"""
import math
import random
import statistics
import unittest


def _window(bars, t, history):
    if t < history or t >= len(bars):
        return None
    w = bars[t - history:t + 1]
    if any(not all(math.isfinite(v) for v in b) for b in w):
        return None
    if any(b[1] <= 0 or b[2] <= 0 or b[3] <= 0 or b[4] <= 0 or
           b[2] < max(b[1], b[4]) or b[3] > min(b[1], b[4])
           for b in w):
        return None
    if any(b[0] >= c[0] for b, c in zip(w, w[1:])):
        return None
    return w


def _sign(x):
    return (x > 0) - (x < 0)


def t1(bars, t):
    """Codex original H1, at close t; None means undefined/skipped."""
    w = _window(bars, t, 20)
    if w is None:
        return None
    c = lambda i: bars[i][4]
    dist = sum(abs(c(i) - c(i-1)) for i in range(t-4, t+1))
    past_range = statistics.mean(bars[i][2] - bars[i][3] for i in range(t-10, t))
    diff = c(t) - c(t-5)
    if not dist or not past_range or not diff:
        return None
    js = []
    for i in range(t-4, t+1):
        hi, lo = bars[i][2], bars[i][3]
        phi, plo = bars[i-1][2], bars[i-1][3]
        union = max(hi, phi) - min(lo, plo)
        if not union:
            return None
        js.append(max(0, min(hi, phi) - max(lo, plo)) / union)
    s = statistics.pstdev(math.log(c(i)/c(i-1)) for i in range(t-19, t+1))
    if s == 0:
        return None
    E, J, amp = abs(diff)/dist, statistics.mean(js), abs(diff)/past_range
    return {'E':E, 'J':J, 'amp':amp, 's20':s, 'd':_sign(diff),
            'event':E >= .75 and J <= .35 and amp >= 1.5}


def t2(bars, t):
    """Claude frozen H1: 20-day quiet/loud split with trailing sigma60."""
    if _window(bars, t, 60) is None:
        return None
    r = lambda i: math.log(bars[i][4]/bars[i-1][4])
    rng = lambda i: (bars[i][2]-bars[i][3])/bars[i-1][4]
    sig = statistics.pstdev(r(i) for i in range(t-59, t+1))
    if sig == 0:
        return None
    m = statistics.median(rng(i) for i in range(t-19, t+1))
    n = sum(r(i) for i in range(t-19, t+1) if rng(i) <= m)
    l = sum(r(i) for i in range(t-19, t+1) if rng(i) > m)
    zn, zl = n/(sig*math.sqrt(10)), l/(sig*math.sqrt(10))
    return {'zN':zn, 'zL':zl, 'T':zn+zl, 'D':zn-zl,
            'quiet_n':sum(rng(i) <= m for i in range(t-19, t+1)),
            'event':zn*zl < 0 and abs(zl) >= 1 and abs(zn) >= .5}


def t3_group(bars, t):
    """Post-comparison interaction: distinguish a neutral quiet signal."""
    a, b = t1(bars,t), t2(bars,t)
    if a is None or b is None or not a['event']:
        return None
    d_n = _sign(b['zN'])
    return 'neutral' if not d_n else ('aligned' if d_n == a['d'] else 'opposed')


def synthetic(mode, count=130):
    rnd = random.Random(202)
    bars = []
    prev = 100.0
    for i in range(count):
        if mode == 'trend':
            end = prev + 1
            open_ = prev
            pad = .1
        elif mode == 'chop':
            end = 100 + 3*math.sin(i/4) + .4*math.cos(i/11)
            open_ = prev
            pad = .25
        elif mode == 'gaps':
            end = prev + (.25 if i % 4 else 1.7)
            open_ = prev + (1.4 if i%9==0 else 0)
            pad = .2
        elif mode == 'flat':
            end = open_ = 100.
            pad = 0.
        elif mode == 'random':
            end = prev * math.exp(rnd.uniform(-.035,.035))
            open_ = prev + rnd.uniform(-.5,.5)
            pad = .1 + rnd.uniform(0,1)
        elif mode == 'neutral':
            delta = (0 if 71 <= i <= 85 else 2.4 if 86 <= i <= 90 else .03 if i % 2 else -.04)
            end = prev + delta
            open_ = prev
            pad = .08
        elif mode == 'conflict':
            delta = (-.12 if 71 <= i <= 85 else 2.4 if 86 <= i <= 90 else .03 if i % 2 else -.04)
            end = prev + delta
            open_ = prev
            pad = .08
        else:
            raise ValueError(mode)
        bars.append((i, open_, max(open_,end)+pad, min(open_,end)-pad, end))
        prev = end
    return bars


class Issue202SyntheticTests(unittest.TestCase):
    def assert_same(self, a, b, keys):
        self.assertEqual(a is None, b is None)
        if a is not None:
            for k in keys:
                if isinstance(a[k], float):
                    self.assertTrue(math.isclose(a[k], b[k], rel_tol=1e-10, abs_tol=1e-10),(k,a[k],b[k]))
                else:
                    self.assertEqual(a[k], b[k])

    def test_future_mask_all_modes(self):
        for mode in ['trend','chop','gaps','random','conflict','neutral','flat']:
            b = synthetic(mode)
            for t in [60,75,90,110]:
                copy = b[:t+1] + [(r[0],r[1]*1.91,r[2]*1.91,r[3]*1.91,r[4]*1.91)
                                     for r in b[t+1:]]
                self.assert_same(t1(b,t),t1(copy,t),['E','J','amp','s20','event','d'])
                self.assert_same(t2(b,t),t2(copy,t),['zN','zL','quiet_n','event'])
                self.assertEqual(t3_group(b,t),t3_group(copy,t))

    def test_rebasing_invariance(self):
        for mode in ['trend','chop','gaps','random','conflict','neutral']:
            b = synthetic(mode)
            scaled = [(i,o*1.77,h*1.77,l*1.77,c*1.77) for i,o,h,l,c in b]
            for t in [60,80,90,110]:
                self.assert_same(t1(b,t),t1(scaled,t),['E','J','amp','s20','event','d'])
                self.assert_same(t2(b,t),t2(scaled,t),['zN','zL','quiet_n','event'])

    def test_manual_trend_t1(self):
        b = synthetic('trend')
        r = t1(b,85)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r['E'],1)
        self.assertAlmostEqual(r['J'], 1/11)
        self.assertAlmostEqual(r['amp'],5/1.2)
        self.assertEqual(r['d'],1)
        self.assertTrue(r['event'])

    def test_t2_parity_independent_partition(self):
        for mode in ['trend','chop','gaps','random','conflict','neutral']:
            b=synthetic(mode)
            for t in [60,75,85,90,115]:
                x=t2(b,t)
                self.assertIsNotNone(x)
                daily=[math.log(b[i][4]/b[i-1][4]) for i in range(t-19,t+1)]
                ranges=[(b[i][2]-b[i][3])/b[i-1][4] for i in range(t-19,t+1)]
                med=sorted(ranges)[9:11]
                split=sum(med)/2
                population=[math.log(b[i][4]/b[i-1][4]) for i in range(t-59,t+1)]
                sig=math.sqrt(sum(v*v for v in population)/60-(sum(population)/60)**2)
                z_n=sum(v for v,v_range in zip(daily,ranges) if v_range<=split)/(sig*math.sqrt(10))
                z_l=sum(v for v,v_range in zip(daily,ranges) if v_range>split)/(sig*math.sqrt(10))
                self.assertAlmostEqual(x['zN'],z_n,places=10)
                self.assertAlmostEqual(x['zL'],z_l,places=10)
                self.assertAlmostEqual(x['T'],sum(daily)/(sig*math.sqrt(10)),places=10)
                self.assertAlmostEqual(x['D'],z_n-z_l,places=10)

    def test_zero_denominator_and_flat(self):
        b=synthetic('flat')
        self.assertIsNone(t1(b,85))
        self.assertIsNone(t2(b,85))
        self.assertIsNone(t3_group(b,85))

    def test_gap_is_valid_and_event_possible(self):
        b=synthetic('gaps')
        self.assertIsNotNone(t1(b,85))
        self.assertIsNotNone(t2(b,85))

    def test_missing_price_skips(self):
        b=synthetic('trend')
        for j in [85,75]:
            copy=list(b)
            i,o,h,l,c=copy[j]
            copy[j]=(i,o,h,l,float('nan'))
            self.assertIsNone(t1(copy,85))
            self.assertIsNone(t2(copy,85))

    def test_duplicate_or_backwards_date_skips(self):
        b=synthetic('trend')
        for bad in [b[83][0], -1]:
            copy=list(b)
            i,o,h,l,c=copy[84]
            copy[84]=(bad,o,h,l,c)
            self.assertIsNone(t1(copy,85))
            self.assertIsNone(t2(copy,85))

    def test_irregular_calendar_spacing_allowed(self):
        b=synthetic('trend')
        b=[(i*3,o,h,l,c) for i,o,h,l,c in b]
        self.assertIsNotNone(t1(b,85))
        self.assertIsNotNone(t2(b,85))

    def test_illegal_ohlc_rejected(self):
        b=synthetic('trend')
        copy=list(b)
        i,o,h,l,c=copy[84]
        copy[84]=(i,o,c-.1,l,c)
        self.assertIsNone(t1(copy,85))
        self.assertIsNone(t2(copy,85))

    def test_insufficient_lookback(self):
        b=synthetic('trend')
        self.assertIsNone(t1(b,19))
        self.assertIsNone(t2(b,59))
        self.assertIsNone(t3_group(b,59))

    def test_range_ties_preserve_frozen_rule(self):
        # Fixed close=100 and H=101 L=99: all 20 days meet R<=median.
        b=[(i,100.,101.,99.,100.) for i in range(130)]
        r=[(b[i][2]-b[i][3])/b[i-1][4] for i in range(66,86)]
        self.assertEqual(sum(v<=statistics.median(r) for v in r),20)
        self.assertIsNone(t2(b,85))  # sigma60=0, event must be skipped.

    def test_t3_real_opposite_possible(self):
        b=synthetic('conflict')
        t=90
        x,y=t1(b,t),t2(b,t)
        self.assertTrue(x['event'])
        self.assertEqual(x['d'],+1)
        self.assertLess(y['zN'],0)
        self.assertGreater(y['zL'],0)
        self.assertEqual(t3_group(b,t),'opposed')

    def test_t3_is_neutral_not_opposed_when_quiet_zero(self):
        b=synthetic('neutral')
        self.assertTrue(t1(b,90)['event'])
        self.assertEqual(t2(b,90)['zN'],0)
        self.assertEqual(t3_group(b,90),'neutral')

    def test_overlapping_events_not_independent(self):
        b=synthetic('trend')
        ev=[t for t in range(60,101) if t1(b,t)['event']]
        self.assertGreater(len(ev),5)
        self.assertTrue(any(b-a<5 for a,b in zip(ev,ev[1:])))
        # This is a caution/fixture; no event-level independent-n claims.


if __name__=='__main__':
    unittest.main()
