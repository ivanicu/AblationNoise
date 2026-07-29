# Amendment 1 — the fitted step location is pinned to the edge of its own search window

Registered 2026-07-29, after the R24 run, before the diagnostic. Commit this file alone.

## What was observed

In `qwen2.5-1.5b` the step fits at **depth `0.889`** on **all ten tests** — five scale-invariant
statistics × two supports — with `p` from `0.0003` to `0.0171`. Ten independent statistics agreeing
on a location reads as a strong localisation.

**It is not one.** `best_step` scans `c` in `[min_side, n - min_side]` with `min_side = 4`, `n = 28`.
So `c = 24` is **the largest split the search permits**, and `24 / 27 = 0.889`. The maximiser is
sitting on the boundary of its own constraint. A boundary argmax is not an estimate of a location;
it is the statement *"at least this far along, and the search could not look further."*

The five statistics agreeing is not evidence either — they are near-deterministic functions of the
same 12 numbers per layer.

## The two worlds

**World A — a real boundary at layer 24.** Something changes between layers 23 and 24 and stays
changed. Prediction: relax `min_side` to 3, 2, 1 and the argmax **stays at 24**; the profile `t(c)`
has an interior peak at 24 and declines for `c > 24`.

**World B — no boundary; a tail that keeps rising.** Concentration climbs through the final layers
with no discontinuity, so the best two-block split is always "as late as allowed." Prediction: the
argmax **tracks the constraint** — 25 at `min_side=3`, 26 at 2, 27 at 1 — and `t(c)` is increasing
over the whole range with no interior peak.

The worlds differ ontologically, not parametrically. A gives the repository a layer index to point
at. B says there is no index to point at and every sentence naming one is wrong.

## Registered rule, committed before the run

Over the ten tests, at `min_side` in `{4, 3, 2, 1}`:

- **BOUNDARY-IS-REAL** — argmax within `±1` of `24` at every `min_side`, in `>= 8` of `10` tests.
- **ARTIFACT** — argmax strictly increases as `min_side` decreases, in `>= 8` of `10` tests.
- **UNVERIFIED** — anything else. Not an acquittal for either world.

## Controls, both required before the real data is read

1. **Planted step at `c = 21`** (`0.75` depth, the profile R24 already generates). At `min_side = 1`
   the unconstrained argmax must land within `±1` of `21`. This proves an interior peak is
   *findable* — without it, an edge argmax on real data carries no information.
2. **Planted flat.** The argmax may be anywhere; `t` at the argmax must not exceed the null median
   by more than the flat control's own `p >= 0.05`. This bounds how big an edge `t` gets for free.

## The confound this diagnostic must not fall into

At `c = 27` one side holds a single layer, and a one-element block makes `t` unstable in the
direction that flatters the artifact reading. So the **full profile is emitted, not the argmax
alone**, and the ARTIFACT rule requires a *monotone* march, which one unstable endpoint cannot
produce on its own.
