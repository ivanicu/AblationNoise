# R7 — AT A FIXED PERTURBATION SIZE, DOES THE *DIRECTION* CHANGE READABILITY?

Written 2026-07-27, before `run.py` exists and before any R7 measurement. R6's verdict and its
diagnostic: `R6_intervention/README.md`.

---

## WHY R6 COULD NOT ANSWER THIS

R6 compared `zero`, `mean` and `resample` and found all three differ — but its own pre-registered
diagnostic showed why that is uninformative: at the final position a head's output is **73–86%
item-independent**, so mean-ablation displaces the residual stream by only **14–27%** of what
zeroing displaces. The three arms were three *magnitudes*, not three *kinds*, and every smaller
effect, smaller floor and dead positive control follows from the smaller perturbation.

**R6 varied the description of the intervention and got a size difference for free.** R7 removes
that degree of freedom by construction.

## THE DESIGN: ONE DISPLACEMENT SIZE, FOUR DIRECTIONS

For item *i* and head *h*, let `x` be the head's final-position output slice and `μ` its mean over
items. Define the **reference displacement** `d = ‖x − μ‖` — the distance mean-ablation actually
moves, per item, per head. Every matched arm writes a point exactly `d` away from `x`:

| arm | writes | direction | ‖displacement‖ |
|---|---|---|---|
| `mean` | `μ` | toward the item-average — **on-distribution** | `d` |
| `shrink` | `x·(1 − d/‖x‖)` | toward the origin — **the zeroing direction** | `d` |
| `randdir` | `x + d·u`, `u` a random unit vector | **no relation to the data** | `d` |
| `zero` | `0` | toward the origin, **all the way** | `‖x‖` |

`zero` is not matched — it is the anchor. It must reproduce R1's `ratio_k1`, exactly as R6's zero
arm did on 4 of 4 models, or the plumbing has changed and nothing else in the round is comparable.

The three matched arms differ **only in direction**. `mean` is on-distribution; `shrink` points the
way zeroing points; `randdir` is off-distribution in a way that is neither.

## THE ESTIMATOR, NAMED IN FULL — AND CHECKED FOR DEGENERACY UNDER EVERY ARM

R4 was withdrawn for naming a gate and leaving the estimator open. R6 named the estimator and named
one that its own new arms drove to a division by zero. So R7 names it **and states, per arm, which
quantity could vanish and why it cannot**:

* **statistic** — `readability(A) = |positive control effect| / band sd(A)`. R6's amended statistic,
  which survived R6 intact.
* **numerator** — every head of the mechanism's layer, ablated under arm `A`. Cannot vanish: the
  matched arms all displace by `d > 0`, and `d` is measured and reported per arm.
* **denominator** — sd over 30 single-head draws in the upper-half band under arm `A`. Cannot
  collapse the way R6's sham did, because **the sham arm is not in the statistic at all.** R6's
  degeneracy came from an early-layer denominator that on-distribution writes barely move; R7's
  denominator is in the same band as its numerator.
* **comparison** — `rr(A) = readability(A) / readability(mean)`, on the matched arms only.
* **aggregation** — median over informative models. Not the mean (R2's heavy tail).
* **inclusion** — R6 conflated two properties and this round separates them. A model enters the
  aggregate iff **both**: (a) its `zero` arm has `ratio_k1 > 1.5`, and (b) its `zero` arm's positive
  control clears its own band sd. Each exclusion is reported with **which** criterion it failed.

## THE MEASUREMENT THAT MAKES THE MATCHING AUDITABLE

Every arm records its **realized** mean displacement norm. This is not bookkeeping: the matching is
the entire design, and a matching asserted in prose rather than measured is the same failure this
repository has now recorded four times.

```
ROUND-INVALIDATING CHECK 1   the three matched arms' realized ||displacement|| agree within 1%
ROUND-INVALIDATING CHECK 2   the zero arm reproduces R1's checked-in ratio_k1 within 10%
ROUND-INVALIDATING CHECK 3   every arm's positive control clears its own band sd
```

Failing any → `NOT MET`, no verdict, non-zero exit. As in R6, a broken arm is not a data point that
went the other way.

## PREDICTION MATRIX

| | `rr(shrink)` | `rr(randdir)` | what it would mean |
|---|---|---|---|
| **D — DIRECTION MATTERS** | ≠ 1 | ≠ 1, and ≈ `rr(shrink)` | off-distribution *as such* changes readability; R1's floor is partly an off-manifold effect and must be described that way |
| **S — SIZE IS ALL** | ≈ 1 | ≈ 1 | at fixed displacement, direction is irrelevant. **The off-distribution objection to R1 is answered: zeroing is not special, it is just large.** R1's floor stands as a fact about perturbation magnitude |
| **M — THE MANIFOLD IS SPECIAL** | ≠ 1 | ≈ `rr(shrink)`, both ≠ 1, and `mean` is the outlier | on-distribution is a distinguished direction; the other two behave alike |

Note that **D and M are separated by `randdir`**, which is the arm R6 did not have. Without it,
"`shrink` differs from `mean`" is compatible with both.

## PRE-REGISTERED GATE

```
SIZE-IS-ALL        median rr(shrink) AND median rr(randdir) both in [0.67, 1.5]
                   AND each within [0.5, 2.0] on at least 3 informative models
                   -> world S. The strongest published objection to R1 is ANSWERED, and the
                      top-level README gains a sentence saying so, with this round's numbers.

DIRECTION-MATTERS  median rr(shrink) or median rr(randdir) outside [0.5, 2.0]
                   -> world D or M; `randdir` decides which. R1's floor is restated as scoped to
                      off-manifold intervention, and the front page is edited in the same commit
                      as the result.

AMBIGUOUS          anything else -> report the distribution, claim neither, name the separator.
```

**Retraction commitment.** If `DIRECTION-MATTERS` fires with `mean` the outlier, R1's headline is
scoped down in the same commit as the result — not deferred, not softened. R6 could not trigger this
clause; R7 is built so that it can.

## COST AND THE REDUCTIONS DECLARED IN ADVANCE

4 arms × (1 baseline + 30 band draws + 1 positive control) × 120 items, at k=1, on 4 models. About
1.3× R6 per model. No new downloads.

* **k=1 only**, as R6. The question is about direction, not set size.
* `randdir`'s unit vectors are drawn once per (item, head) from a fixed seed and **reported**, so the
  arm is reproducible rather than merely random.
* If fewer than **3** models satisfy both inclusion criteria, R7 reports what it has and returns
  `NOT MET`. Same clause as R2, R3 and R6, for the same reason.

## WHAT MAKES THIS WORTH THE COMPUTE

R1's headline has exactly one serious published objection: *zeroing is off-manifold, so of course
everything moves.* R6 tried to answer it and produced a magnitude confound instead. R7 is the
smallest design in which the objection is decidable — and under world S it is **answered in R1's
favour by an experiment that was built to break it**, which is worth more than the original result.
