# Amendment 2 — the control validated a quantity the round never reads

Registered 2026-07-29, after control 1 failed three times, before any rerun. Committed alone.

**This is a LOOSENING and is registered as one.** It relaxes the control on exactly the item-cells where
it currently fails. The justification has to be the estimand, not the fact that it would pass, so the
justification is stated first and the outcome is not known when this file is committed.

## The estimand mismatch

`κ` is built from

```
P_{ℓ,h} = log | mean_i ⟨ a_{ℓ,h,i} , g_{ℓ,h,i} ⟩ |
```

— the **item mean** of the inner product. Nothing downstream reads a per-item `⟨a,g⟩_i`.

Control 1 as registered and as amended once tests **per-item** derivatives: for each of four items
separately, the relative error of `Δmargin_i(α)/α` against `⟨a,g⟩_i`, then `max` over items for the
threshold and `AND` over items for the band.

A relative error has the per-item value in its denominator. When `⟨a,g⟩_i ≈ 0` — which happens, and which
is exactly the sign-cancellation this round exists to measure — that ratio blows up without anything being
wrong with the derivative. `L09H03` reaches `5.480e-01` that way while `L09H00`, on the same run, gives
ratios `2.06 2.04 2.02 2.00 2.06` and an `O(α)` extrapolation accurate to `0.912`.

So the control is not conservative. It is a **different test**, strict in a direction the analysis never
travels, and its failures carry no information about `P`.

## The replacement

Test the finite-difference limit on the quantity `P` actually takes:

```
FD(α) = mean_i ( bm_i − margin_i(α) ) / α          over the same 120 items the round uses
target = mean_i ⟨ a_{ℓ,h,i} , g_{ℓ,h,i} ⟩
```

AMENDMENT_1's two conditions are carried over **unchanged in form**, now applied to this single sequence
per cell rather than to four per-item sequences:

1. `min` over `α` of `|FD(α) − target| / |target| ≤ 1%`.
2. Halving ratios inside `[1.6, 2.4]` for consecutive pairs from `α = 1` down to the pair preceding the
   `argmin`.

`float64` on CPU, as in `gate1_fd64.py`, because the `float32` roundoff floor is independently
established and would otherwise re-enter.

## Why this is a loosening, precisely, and what remains able to fail

- **Loosened:** a cell no longer fails because one item of four has a near-zero denominator. The mean's
  denominator is `|mean_i ⟨a,g⟩|`, which is near zero only if the cell's *aggregate* effect is near zero
  — and such a cell is dropped from `κ` anyway, since `P` would be undefined.
- **Not loosened:** the `1%` bar and the `[1.6, 2.4]` band are the same numbers. A gradient hooked one
  module later would be wrong by roughly `cond(W_O) = 5.5` (R6's measured value for this block) at every
  `α`, and would fail condition 1 at every `α` and condition 2 by having no decreasing regime at all.
- **Newly able to fail:** `120` items instead of `4`, so the mean is a much lower-variance target and the
  band has less slack, not more. A cell whose per-item errors happened to average out cannot hide here —
  the mean is what is being differenced on both sides.

## What is not being changed

The three worlds, the prediction matrix, all four decision thresholds, control 2, the curvature control
and the stopping rule are untouched. **No `κ` has been read in any of the three runs so far**, so there is
no result that a loosened control would rescue — the only circumstance in which loosening one is
legitimate at all, and the reason this amendment can be written honestly rather than defensively.

## If it fails again

Then the first-order account cannot be validated on this task at this precision even on the estimand it
targets, `κ` is not read a fourth time, and **that is the round's result**: the per-head ablation effect is
not certifiably a first-order quantity, which is world B's ontology arriving through the control rather
than through the prediction matrix. It would be reported as exactly that, and not as a null.
