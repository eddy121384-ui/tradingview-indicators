"""Tests for the A9 market-structure dimension audit (frozen A9-r2 prereg).

Proves, on synthetic fixtures plus one real frozen OOS3 file: frozen Core-2
reuse, causal self-exclusion of every percentile, D3 measurement causality,
D4 exactness and frozen lookback, append-future invariance for all four
dimensions, stock boundaries, exact bins, strictly-future outcomes, exact
MFE/MAE windows, HMM sequence boundaries, K selection without outcomes, HMM
train/test chronology, deterministic rebuild, and scalar-vs-vectorised EM
equivalence. No A9 outcome table is produced here.

Run with: `python -m pytest -q test_issue78_market_structure_a9.py`
or directly: `python test_issue78_market_structure_a9.py`.
"""
from __future__ import annotations

import inspect
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_causal_core2_a4 as a4
import analyze_issue78_market_structure_a9 as a9

HERE = Path(__file__).resolve().parent


def _synth_close(n: int = 420, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 100.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.011, n)))


def _ready(n: int) -> np.ndarray:
    return np.ones(n, dtype=bool)


# 1 -------------------------------------------------------------------------
def test_core2_import_reuse_unchanged():
    assert a9.causal_prior_pct is a4.causal_prior_pct
    assert a9.WARMUP_MIN == a4.WARMUP_MIN == 252
    assert inspect.getsourcefile(a9.a4).endswith("analyze_issue78_causal_core2_a4.py")
    src = inspect.getsource(a9.build_structure_frame)
    assert "a4.add_causal_ranks" in src
    assert "a2.add_within_stock_ranks" in src
    assert "a2.build_sd_frame" in src
    a4_src = inspect.getsource(a4.causal_prior_pct)
    assert "bisect_left" in a4_src and "0.5 * (right - left)" in a4_src


# 2 -------------------------------------------------------------------------
def test_core2_causal_percentile_excludes_current_bar():
    vals = np.linspace(1.0, 10.0, 300)
    pct = a4.causal_prior_pct(vals, _ready(300))
    assert np.isnan(pct[:252]).all()
    assert np.isfinite(pct[252:]).all()
    assert (pct[252:] > 0.99).all()
    # a duplicate of an old value scores by prior mass only (self excluded)
    vals2 = vals.copy()
    vals2[280] = vals[100]
    pct2 = a4.causal_prior_pct(vals2, _ready(300))
    assert pct2[280] < pct[280]
    expected = (100 + 0.5) / 280.0
    assert abs(pct2[280] - expected) < 1e-12


# 3 -------------------------------------------------------------------------
def test_d3_measure_uses_only_current_and_past():
    close = _synth_close()
    rv = a9.realized_vol(close)
    assert np.isnan(rv[:20]).all()
    assert np.isfinite(rv[20:]).all()
    close2 = close.copy()
    close2[350] *= 1.5
    rv2 = a9.realized_vol(close2)
    np.testing.assert_allclose(rv[:350], rv2[:350], equal_nan=True)
    assert rv[350] != rv2[350]
    # exact formula: ddof=1 stdev of 20 log-return increments ending at t
    t = 100
    inc = np.diff(np.log(close[t - 20: t + 1]))
    assert abs(rv[t] - np.std(inc, ddof=1)) < 1e-12
    assert len(inc) == 20


# 4 -------------------------------------------------------------------------
def test_d3_percentile_excludes_current_and_future():
    vals = np.linspace(0.01, 0.5, 400)
    pct = a4.causal_prior_pct(vals, _ready(400))
    vals2 = vals.copy()
    vals2[300:] = 99.0
    pct2 = a4.causal_prior_pct(vals2, _ready(400))
    # earlier bars never see the rewritten current/future observations
    np.testing.assert_allclose(pct[:300], pct2[:300], equal_nan=True)
    # the reference set excludes the current bar: a current value above every
    # prior value ranks 1.0 exactly (it cannot dilute its own denominator) and
    # the next bar also sees it as a prior value only
    assert pct2[300] == 1.0
    # bar 301 sees bar 300 only as a *prior* value, tie-averaged
    assert abs(pct2[301] - 300.5 / 301.0) < 1e-12
    # strictly increasing history => rank exactly 1.0, i.e. self excluded
    inc = np.arange(300.0)
    pct3 = a4.causal_prior_pct(inc, _ready(300))
    assert np.allclose(pct3[252:], 1.0)


# 5 -------------------------------------------------------------------------
def test_d4_formula_exact_on_deterministic_fixture():
    line = np.linspace(100.0, 120.0, 40)
    er = a9.efficiency_ratio(line)
    assert abs(er[20] - 1.0) < 1e-12
    round_trip = np.concatenate(
        [np.linspace(100.0, 110.0, 11), np.linspace(110.0, 100.0, 10)]
    )
    assert abs(a9.efficiency_ratio(round_trip)[20]) < 1e-12
    assert math.isnan(a9.efficiency_ratio(np.full(40, 100.0))[20])
    close = _synth_close(120)
    t = 60
    num = abs(close[t] - close[t - 20])
    den = np.abs(np.diff(close[t - 20: t + 1])).sum()
    assert abs(a9.efficiency_ratio(close)[t] - num / den) < 1e-12


# 6 -------------------------------------------------------------------------
def test_d4_uses_exactly_frozen_lookback():
    close = _synth_close(160)
    t = 100
    er = a9.efficiency_ratio(close)
    closer = close.copy()
    closer[t - 21] *= 1.3
    assert a9.efficiency_ratio(closer)[t] == er[t]
    inside = close.copy()
    inside[t - 20] *= 1.3
    assert a9.efficiency_ratio(inside)[t] != er[t]
    assert a9.efficiency_ratio(close, span=21)[t] != er[t]


# 7 -------------------------------------------------------------------------
def test_d4_percentile_excludes_current_and_future():
    rng = np.random.default_rng(21)
    er = rng.random(400) * 0.5 + 0.1
    pct = a4.causal_prior_pct(er, _ready(400))
    er2 = er.copy()
    er2[320:] = 5.0
    pct2 = a4.causal_prior_pct(er2, _ready(400))
    np.testing.assert_allclose(pct[:320], pct2[:320], equal_nan=True)
    assert pct2[320] == 1.0
    # bar 321 sees bar 320 only as a *prior* value, tie-averaged
    assert abs(pct2[321] - 320.5 / 321.0) < 1e-12


# 8 -------------------------------------------------------------------------
def test_append_future_invariance_all_four_dimensions():
    rng = np.random.default_rng(31)
    n = 500
    close = _synth_close(n, seed=32)
    high, low = close * 1.01, close * 0.99
    atr = a9.wilder_atr(high, low, close)
    rv = a9.realized_vol(close)
    er = a9.efficiency_ratio(close)
    core = np.linspace(-3.0, 3.0, n)
    pct = a4.causal_prior_pct(core, _ready(n))

    extra = 30
    fut = close[-1] * np.exp(np.cumsum(rng.normal(0, 0.01, extra)))
    close2 = np.concatenate([close, fut])
    high2 = np.concatenate([high, fut * 1.01])
    low2 = np.concatenate([low, fut * 0.99])
    core2 = np.concatenate([core, rng.normal(size=extra)])
    atr2 = a9.wilder_atr(high2, low2, close2)
    rv2 = a9.realized_vol(close2)
    er2 = a9.efficiency_ratio(close2)
    pct2 = a4.causal_prior_pct(core2, _ready(n + extra))
    for before, after in ((atr, atr2), (rv, rv2), (er, er2), (pct, pct2)):
        np.testing.assert_allclose(before, after[:n], equal_nan=True)


# 9 -------------------------------------------------------------------------
def test_stock_boundaries_preserved():
    a = np.linspace(0.0, 1.0, 300)
    b = np.full(300, 1000.0)
    pa = a4.causal_prior_pct(a, _ready(300))
    pb = a4.causal_prior_pct(b, _ready(300))
    assert np.isfinite(pa[252:]).all()
    # a constant series has pct exactly 0.5: no foreign values in the reference
    assert np.allclose(pb[252:], 0.5)
    assert not np.allclose(np.nan_to_num(pa, nan=-1), np.nan_to_num(pb, nan=-1))
    idx = np.array([0, 1, 2, 10, 11, 20])
    assert [list(r) for r in a9.contiguous_runs(idx)] == [[0, 1, 2], [10, 11], [20]]
    assert a9.WARMUP_MIN == 252


# 10 ------------------------------------------------------------------------
def test_bin_assignments_exact_at_frozen_boundaries():
    ranks = np.array([0.0, 0.30, 0.3000001, 0.5, 0.6999999, 0.70, 1.0, np.nan])
    assert list(a9._bin_pct(ranks)) == [
        "LOW", "LOW", "MID", "MID", "MID", "HIGH", "HIGH", "",
    ]
    assert list(a9._bin_code(ranks)) == [0, 0, 1, 1, 1, 2, 2, -1]
    hard = np.array([0.20, 0.2000001, 0.79, 0.80])
    assert a9.HARD_LOW == 0.20 and a9.HARD_HIGH == 0.80
    assert a9.LOW_MAX == 0.30 and a9.HIGH_MIN == 0.70
    assert hard[0] <= a9.HARD_LOW and hard[3] >= a9.HARD_HIGH


# 11 ------------------------------------------------------------------------
def test_forward_outcomes_begin_strictly_after_observation():
    n = 80
    close = 100.0 * np.exp(np.cumsum(np.full(n, 0.01)))
    logc, scale = np.log(close), np.full(n, 0.02)
    out = pd.DataFrame(index=range(n))
    a9.add_path_outcomes(out, logc, close, scale)
    t, h = 20, 5
    assert abs(out["lret_5"][t] - (logc[t + 5] - logc[t])) < 1e-12
    # a move inside the window changes path-shape outcomes
    logc_in = logc.copy()
    logc_in[t + 3] += 0.5
    out_in = pd.DataFrame(index=range(n))
    a9.add_path_outcomes(out_in, logc_in, close, scale)
    for col in ("fvol_5", "mfe_5", "mfe_raw_5"):
        assert out_in[col][t] != out[col][t]
    # a level shift at t (the observation bar) never enters an endpoint return
    logc_now = logc.copy()
    logc_now[t] += 0.5
    out_now = pd.DataFrame(index=range(n))
    a9.add_path_outcomes(out_now, logc_now, close, scale)
    assert out_now["lret_5"][t] != out["lret_5"][t]  # both endpoints shifted
    assert out["fvol_5"][t] < 1e-12  # flat +1%/bar path has no dispersion
    # a move beyond the window never changes the h-window outcomes
    logc_after = logc.copy()
    logc_after[t + h + 1] += 0.5
    out_after = pd.DataFrame(index=range(n))
    a9.add_path_outcomes(out_after, logc_after, close, scale)
    for col in ("lret_5", "abs_5", "fvol_5", "mfe_5", "mae_5", "mfe_raw_5"):
        assert out_after[col][t] == out[col][t]


# 12 ------------------------------------------------------------------------
def test_mfe_mae_windows_exact():
    n = 60
    close = 100.0 + np.arange(n, dtype=float)
    logc, scale = np.log(close), np.full(n, 0.05)
    out = pd.DataFrame(index=range(n))
    a9.add_path_outcomes(out, logc, close, scale)
    t = 7
    for h in (1, 5, 10, 20):
        seg = logc[t + 1: t + h + 1] - logc[t]
        assert len(seg) == h
        assert abs(out[f"mfe_{h}"][t] - seg.max() / 0.05) < 1e-12
        assert abs(out[f"mae_{h}"][t] - seg.min() / 0.05) < 1e-12
        assert abs(out[f"mfe_raw_{h}"][t] - seg.max()) < 1e-12
        if h > 1:
            inc = np.diff(logc[t: t + h + 1])
            assert abs(out[f"fvol_{h}"][t] - np.std(inc, ddof=1)) < 1e-12
        else:
            assert math.isnan(out["fvol_1"][t])
    # future ER uses the forward 20-bar path only
    t20 = 5
    seg = close[t20: t20 + 21]
    manual = abs(seg[-1] - seg[0]) / np.abs(np.diff(seg)).sum()
    assert abs(out["futer_20"][t20] - manual) < 1e-12


# 13 ------------------------------------------------------------------------
def _seq_ll(seq: np.ndarray, model: dict) -> float:
    logB = a9._log_emissions(seq, model["mu"], model["var"])
    logA = np.log(model["A"] + 1e-300)
    logpi = np.log(model["pi"] + 1e-300)
    alpha = logpi + logB[0]
    for t in range(1, len(seq)):
        alpha = logB[t] + a9._logsumexp(alpha[:, None] + logA, axis=0)
    return float(a9._logsumexp(alpha))


def test_hmm_sequence_boundaries_prevent_cross_stock_transitions():
    # two well-separated clusters, explicit params: posteriors are deterministic
    lo = np.full((2, 1), -6.0)
    hi = np.full((2, 1), +6.0)
    pi = np.array([0.5, 0.5])
    A0 = np.array([[0.9, 0.1], [0.1, 0.9]])
    mu = np.array([[-6.0], [+6.0]])
    var = np.array([[0.09], [0.09]])
    # separate sequences: the only transitions are 0->0 and 1->1
    _, _, A_sep, _, _ = a9._em_step_scalar(
        [lo, hi], pi.copy(), A0.copy(), mu.copy(), var.copy()
    )
    _, _, A_sep_fast, _, _ = a9._em_step_fast(
        [lo, hi], pi.copy(), A0.copy(), mu.copy(), var.copy()
    )
    assert A_sep[0, 1] < 1e-12 and A_sep[1, 0] < 1e-12
    assert A_sep_fast[0, 1] < 1e-12 and A_sep_fast[1, 0] < 1e-12
    np.testing.assert_allclose(A_sep, A_sep_fast, atol=1e-12)
    # the same bars concatenated add the 0->1 junction transition, which the
    # boundary-respecting step must not see
    _, _, A_cat, _, _ = a9._em_step_scalar(
        [np.concatenate([lo, hi])], pi.copy(), A0.copy(), mu.copy(), var.copy()
    )
    assert A_cat[0, 1] > 0.4
    # likelihood identity: the step's ll is the sum over separate sequences
    ll_sep = a9._em_step_scalar(
        [lo, hi], pi.copy(), A0.copy(), mu.copy(), var.copy()
    )[0]
    params = {"A": A0, "mu": mu, "var": var, "pi": pi}
    assert abs(ll_sep - (_seq_ll(lo, params) + _seq_ll(hi, params))) < 1e-9
    # no transitions at all in length-1 sequences
    _, _, A_one, _, _ = a9._em_step_scalar(
        [np.array([[-6.0]]), np.array([[+6.0]])],
        pi.copy(), A0.copy(), mu.copy(), var.copy(),
    )
    np.testing.assert_allclose(A_one, A0)
    fit = a9._em_fit([lo, hi], 2, verbose=False)
    assert fit["n_transitions"] == 1 + 1
    # sequence construction: stocks and gaps are separate sequences
    entries = [
        {"figi": "A", "train_mask": np.array([True] + [False] + [True] * 3 + [False]),
         "coords": np.zeros((6, 4))},
        {"figi": "B", "train_mask": np.ones(4, dtype=bool),
         "coords": np.zeros((4, 4))},
    ]
    seqs = a9.hmm_train_sequences(entries)
    assert [len(s) for s in seqs] == [3, 4]


# 14 ------------------------------------------------------------------------
def test_hmm_k_selected_without_outcomes():
    params = list(inspect.signature(a9._em_fit).parameters)
    assert "seqs" in params and "n_states" in params
    assert not any("outcome" in p or "forward" in p or "return" in p for p in params)
    fake = [
        {"K": 2, "bic": 120.0},
        {"K": 3, "bic": 90.0},
        {"K": 4, "bic": 95.0},
        {"K": 5, "bic": 99.0},
    ]
    best = min(fake, key=lambda f: (round(f["bic"], 9), f["K"]))
    assert best["K"] == 3
    tied = [{"K": 4, "bic": 50.0}, {"K": 2, "bic": 50.0}]
    assert min(tied, key=lambda f: (round(f["bic"], 9), f["K"]))["K"] == 2
    # BIC = -2 ll + n_params ln(n)
    model = a9._em_fit([np.random.default_rng(1).normal(0, 1, (60, 2))], 2,
                       verbose=False)
    manual = -2 * model["train_ll"] + model["n_params"] * math.log(model["n_train"])
    assert abs(model["bic"] - manual) < 1e-9
    assert model["n_params"] == (2 - 1) + 2 * 2 * 2 + 2 * (2 - 1)


# 15 ------------------------------------------------------------------------
def test_hmm_train_test_chronology_exact():
    cut = np.datetime64(a9.HMM_TRAIN_END)
    dates = np.array(
        ["2014-12-31", "2015-01-01", "2015-01-02", "2016-06-01"],
        dtype="datetime64[D]",
    )
    ready = np.ones(4, dtype=bool)
    train_mask = ready & (dates < cut)
    split = (dates >= cut).astype(np.int8)
    assert list(train_mask) == [True, False, False, False]
    assert list(split) == [0, 1, 1, 1]
    assert int((train_mask & (split == 1)).sum()) == 0
    # the scaler uses training bars only
    rng = np.random.default_rng(51)
    train = rng.normal(0, 1, (30, 4))
    evaluate = rng.normal(50, 1, (30, 4))
    entries = [
        {"figi": "A", "coords": np.vstack([train, evaluate]),
         "train_mask": np.array([True] * 30 + [False] * 30)},
    ]
    _, _, mean, std, _ = a9.fit_hmm(entries, ks=(2,), verbose=False)
    np.testing.assert_allclose(mean, train.mean(axis=0))
    np.testing.assert_allclose(std, train.std(axis=0))
    assert not np.allclose(mean, 50.0, atol=1.0)


# 16 ------------------------------------------------------------------------
def test_deterministic_rebuild_and_em_equivalence():
    rng = np.random.default_rng(61)
    seqs = [rng.normal(-1, 0.7, (40, 3)), rng.normal(2, 0.7, (55, 3))]
    pi, A, mu, var = a9._init_params(seqs, 3)
    s1 = a9._em_step_scalar(seqs, pi.copy(), A.copy(), mu.copy(), var.copy())
    s2 = a9._em_step_fast(seqs, pi.copy(), A.copy(), mu.copy(), var.copy())
    assert abs(s1[0] - s2[0]) < 1e-6 * max(1.0, abs(s1[0]))
    for left, right in zip(s1[1:], s2[1:]):
        np.testing.assert_allclose(left, right, rtol=1e-8, atol=1e-10)
    f1 = a9._em_fit(seqs, 3, verbose=False)
    f2 = a9._em_fit(seqs, 3, verbose=False)
    np.testing.assert_allclose(f1["mu"], f2["mu"])
    assert f1["bic"] == f2["bic"]


def test_deterministic_real_data_rebuild():
    from smoke_issue119_frozen_classifier import load_classifier

    raw_dir = (
        HERE / "artifacts" / "issue78_equity_proof_policy_oos3" / "snapshot" / "raw"
    )
    raws = sorted(raw_dir.glob("*.csv.gz"))
    assert len(raws) == 300, f"expected recovered OOS3 snapshot, got {len(raws)}"
    classifier, _ = load_classifier(HERE / "generated" / "wyckoff-issue78-rc-python.py")
    raw = pd.read_csv(raws[0])
    f1 = a9.build_structure_frame(raw, classifier)
    f2 = a9.build_structure_frame(raw, classifier)
    for col in ("rv20", "natr20", "er20", "rank_c_d3", "rank_c_d3_rob",
                "rank_c_d4", "futer_20", "mfe_10", "mae_10"):
        np.testing.assert_array_equal(
            np.nan_to_num(f1[col].to_numpy(float), nan=-999.0),
            np.nan_to_num(f2[col].to_numpy(float), nan=-999.0),
        )
    assert (f1["atlas_ready"].to_numpy() == f2["atlas_ready"].to_numpy()).all()
    # A9 eligibility never admits a bar Core-2 rejects
    assert int((f1["d3_ready"] & ~f1["ready"]).sum()) == 0
    assert int((f1["d4_ready"] & ~f1["ready"]).sum()) == 0
    assert int((f1["atlas_ready"] & ~f1["causal_ready"]).sum()) == 0


# extra: the gap-safe Wilder ATR repair ------------------------------------
def test_wilder_atr_survives_interior_gap():
    rng = np.random.default_rng(71)
    n = 120
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    high, low = close * 1.01, close * 0.99
    full = a9.wilder_atr(high, low, close)
    # blank one interior bar (the 2001-09-11 failure mode)
    k = 60
    close_g, high_g, low_g = close.copy(), high.copy(), low.copy()
    close_g[k] = high_g[k] = low_g[k] = np.nan
    gapped = a9.wilder_atr(high_g, low_g, close_g)
    assert np.isfinite(gapped[k + 1:]).all()
    # dropping the unusable bar reproduces the same ATR afterwards
    dropped = a9.wilder_atr(
        np.delete(high, k), np.delete(low, k), np.delete(close, k)
    )
    np.testing.assert_allclose(gapped[k + 1:], dropped[k:], equal_nan=True)
    assert not np.isnan(full[k])


def test_publication_ready_frozen_constants():
    assert a9.HMM_KS == (2, 3, 4, 5)
    assert a9.HMM_TRAIN_END == "2015-01-01"
    assert a9.GATE_PROPS == (
        "fwd_10", "lret_10", "abs_10", "fvol_10", "mfe_10", "mae_10",
        "cont_10", "rev_10", "futer_20",
    )
    assert a9.NOVEL_SPEARMAN_MAX == 0.50 and a9.NOVEL_MI_MAX == 0.10
    prereg = (
        HERE / "decisions" / "issue-78-market-structure-a9-preregistration.md"
    ).read_text(encoding="utf-8")
    for token in ("rv20", "natr20", "ER20", "0.30", "0.70", "2015-01-01",
                  "KEEP_AS_ATLAS_DIMENSION", "HMM_ADDS_STABLE_STRUCTURE"):
        assert token in prereg, token


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    raise SystemExit(1 if failures else 0)
