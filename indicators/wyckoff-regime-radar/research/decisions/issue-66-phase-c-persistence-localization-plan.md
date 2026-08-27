# Issue #66 Phase C — Candidate→Formal Persistence Localization Plan

Status: **preregistered diagnostic only / reused frozen data / no PnL / no classifier formula change**

## Question

After accepted B-7, the classifier-facing numeric layers are nearly reciprocal-symmetric while Candidate display is ~99.65% mirrored and Formal stage is only ~92.33% mirrored.

This phase asks:

1. Which residual current-bar inputs create the remaining Candidate/strong-candidate mismatches?
2. Is the Candidate→Formal inertia loop itself directionally non-isomorphic, or does it merely amplify rare upstream mismatches through confirmation/state carry?
3. Which persistence mechanism (confirmation window, fast-switch confirmation, delayed chaos reset, retained confirmed state) accounts for the amplification?

## Frozen parent

Parent = accepted Issue #66 Phase B-7 core.

All B-1/B-2/B-3/B-5/B-6/B-7 repairs are frozen for this diagnostic.

## No formula changes

Phase C may not alter:

- raw stage formulas;
- stage gates;
- probability/evidence thresholds;
- Candidate conflict clauses;
- chaos/coexist logic;
- fast-switch logic;
- confirmation bars;
- inertia/persistence loop;
- any strategy/PnL concept.

## Decomposition

For each of the four frozen FX fixtures and its reciprocal OHLC quote, measure after the same rank warmup:

### Current-bar Candidate inputs

- top-stage mirror agreement;
- probability-valid (`has_sharp`) agreement;
- dominant-weight threshold-pass agreement;
- top-gap threshold-pass agreement;
- evidence threshold-pass agreement;
- `candidate_conflict` agreement;
- `strong_candidate` agreement;
- strong-stage-id mirror agreement (`top_id` only when strong);
- `chaos` agreement;
- `fast_switch` agreement;
- active confirmation-bars agreement.

Every strong-stage mismatch must be attributable to at least one current-bar input mismatch.

### Persistence amplification

Measure:

- Candidate-display mismatch bars and episodes;
- strong-stage mismatch bars and episodes;
- Formal mismatch bars and episodes;
- Formal/strong-stage mismatch amplification ratio;
- share of Formal mismatch bars occurring while all current loop inputs are mirrored (state-carry share).

### Counterfactual replays (diagnostic only)

Using the same B-7 current-bar outputs, replay:

1. original inertia loop (must reproduce `formal_id` exactly);
2. fixed-confirm replay (disable fast-switch shortening only);
3. no-confirmation replay (strong candidate confirms immediately; keep delayed chaos reset);
4. immediate-chaos-reset replay (keep confirmation; chaos clears immediately);
5. confirmation-only replay (confirm repeated strong candidate, but do not retain a prior regime when current strong candidate disappears);
6. stateless strong-stage output.

These are localization probes only. Their Formal agreement is not authorization to adopt any variant.

## Structural symmetry test

The generic replay loop must be tested with synthetic mirrored stage/control inputs. If it produces exact mirrored Formal output under exact mirrored inputs, persistence is structurally direction-neutral and may only be an amplifier of upstream residual mismatch.

## Decision rule

No automatic repair is authorized by Phase C.

The report must identify:

- the dominant source(s) of strong-stage mismatch;
- whether the inertia loop is structurally symmetric under exact mirrored inputs;
- the dominant amplification mechanism by counterfactual/replay evidence.

Only then may a single Phase C repair family be preregistered.

Candidate/Formal improvements from any counterfactual replay are diagnostic evidence only and may not be used for threshold shopping.
