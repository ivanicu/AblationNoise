# R8 — is it the *direction relative to the data*, or *which component* gets destroyed?

Written 2026-07-28, before `run.py` exists and before any R8 measurement.
R7's verdict, its amendment, and its `NOT MET`: `R7_norm_matched/`.

---

## THE GAP R7 LEFT, AND WHY IT LEFT IT

R7 matched the displacement to **0.00%** and found the readability order `mean < randdir < shrink`
in **4 of 4** cells. What it could not say is *why* — because
[R7 AMENDMENT 1](../R7_norm_matched/AMENDMENT_1_two_worlds_had_one_row.md) found that two of its
three pre-registered worlds had **identical rows**:

* *off-distribution as such changes readability*
* *the data manifold is a distinguished direction*

Two sentences, one prediction. R7's design cannot separate them, and neither can more of R7.

## THE AXIS THEY ACTUALLY DIFFER ON

They differ in **which component of the head's output the intervention destroys** — and R6 already
measured that a head's final-position output splits cleanly into two parts, because it is
**73–86% item-independent**:

```
x  =  mu            +   (x - mu)
      item-CONSTANT     item-VARYING        ||x - mu|| / ||x|| = 0.14 - 0.27
```

| arm | what it destroys |
|---|---|
| `mean` | the item-**varying** part; leaves the constant one intact |
| `shrink` | **both**, in proportion |
| `randdir` | **neither** — it only adds |
| **`constant_only`** | the item-**constant** part; leaves the varying one intact |

`constant_only` is the complement of `mean`, and it is the arm R7 did not have.

```
constant_only     x  <-  x − (d / ‖μ‖) · μ            ‖displacement‖ = d
```

It removes the same **length** along the constant direction that `mean` removes along the varying
direction. Not the whole constant component — that would displace by `‖μ‖`, which is 4–7× larger
and would rebuild R6's magnitude confound.

## PREDICTION MATRIX — ROWS COMPARED AS VECTORS, NOT READ AS SENTENCES

This is the check R7 skipped on its own matrix, and it is mechanical: write the rows, compare them
as tuples, and refuse any two that are equal.

| | `readability(constant_only)` relative to | | |
|---|---|---|---|
| | `mean` | `shrink` | `randdir` |
| **C — DESTROYING THE ITEM-CONSTANT PART IS WHAT MATTERS** | ≫ | ≈ | > |
| **F — BEING OFF THE DATA MANIFOLD IS WHAT MATTERS** | ≈ | ≪ | ≪ |
| **V — DESTROYING *ANY* STRUCTURED PART MATTERS; ADDING DOES NOT** | ≫ | ≈ | ≫ |

`(≫, ≈, >)`, `(≈, ≪, ≪)`, `(≫, ≈, ≫)` — three distinct tuples. **C and V differ only in the
`randdir` column**, which is why `randdir` is carried over from R7 rather than dropped as settled.

## THE ESTIMATOR — AND THE VALIDITY RULE IS SCOPED TO IT THIS TIME

**Primary statistic: the within-cell ORDER of `readability(A) = |positive control| / band sd(A)`
across the four matched arms.** Pre-registered as the endpoint, not adopted afterwards — R7 reported
an order as a secondary observation and this round promotes it, with the reason stated before any
R8 number exists: it is a within-cell comparison over the same model, items and draws, so it needs
no ratio, no cross-model aggregation, and no inclusion rule.

**The validity rule changes, and the justification is written before the run rather than after two
`NOT MET`s.** R6 and R7 both declared an entire cell invalid when any arm's positive control failed
to clear its own band sd. That was correct **for a ratio**: a dead denominator inflates it without
bound, which is exactly how R6's `ratio_k1` reached 2133×. It is **not** correct for an ordering. An
arm whose positive control sits below its own floor has a readability below 1, and that is a
measurement — it belongs at the bottom of the order, which is where it would go anyway.

> So: **a dead arm invalidates any RATIO in which it is the denominator, and nothing else.** The
> ordering is computed over all four arms; every ratio is reported against `zero`, the largest
> perturbation and the only arm that has never died in two rounds; `mean` is never a denominator.
>
> This is a loosening and it is named as one. The defence is that it attaches the rule to the
> statistic it protects instead of to the cell, and that both parts were true before R8 ran: R7's
> ordering was already identical in the two cells its own gate had to drop.

Everything else carries over unchanged: `DRAW_SEED = 20260727`, k=1, 30 band draws, the upper-half
band, `readability`, median over models, and R1's live-sham inclusion rule.

## ROUND-INVALIDATING CHECKS

```
CHECK 1   the four matched arms' realized ||displacement|| agree within 1%
CHECK 2   the zero arm reproduces R1's checked-in ratio_k1 within 10%
CHECK 3   the `shrink` and `constant_only` overshoot counts are reported, per model, and any
          cell with a non-zero count is excluded from the ORDER claim rather than silently kept
```

CHECK 3 is new and it comes from R7, where 102 head-writes had `d > ‖x‖` and `shrink`'s step passed
*through* the origin — displacement norm still exactly `d`, CHECK 1 still passing, the arm silently
mislabelled. `constant_only` has the same failure mode when `d > ‖μ‖`. Counted per arm, and this
time a non-zero count **excludes the cell from the order claim** instead of being reported beside it.

## PRE-REGISTERED GATE

```
COMPONENT       readability(constant_only) >= readability(shrink) x 0.7  AND  >= 2x mean's
                on at least 3 order-eligible models  -> world C or V; randdir decides which.
                The finding is about WHICH PART is destroyed, not about the manifold.

MANIFOLD        readability(constant_only) <= readability(mean) x 1.5  AND  <= half of randdir's
                on at least 3 order-eligible models  -> world F. On-manifold-ness is the axis, and
                R1's floor is restated as scoped to off-manifold intervention IN THE SAME COMMIT
                as the result.

AMBIGUOUS       anything else -> report the orders, claim neither, name the next separator.
```

**Order-eligible** = zero-arm `ratio_k1 > 1.5` (R1's live sham) **and** zero overshoot on both
truncating arms. Reported per model with which criterion failed.

## COST

5 arms × (1 baseline + 30 band + 30 sham + 1 positive control) × 120 items × 4 models — about 1.25×
R7. No new downloads. If fewer than 3 models are order-eligible, R8 reports what it has and returns
`NOT MET`; the same clause as R2, R3, R6 and R7, and it has now bitten twice, which is the cost of
having written it.
