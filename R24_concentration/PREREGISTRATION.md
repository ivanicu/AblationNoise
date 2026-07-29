# Pre-registration — CONCENTRATION, and whether depth is a gradient or a boundary

Written 2026-07-29, **before the statistic was computed**, committed alone.

## Why the object changed again

`R23` asked whether the ablation-effect distribution has a *shape* that varies. Its verdict was
withdrawn: the descriptors were top-order statistics in disguise (`q99` at `n = 12` interpolates to
index `11.89` of `12` — it is the maximum), four of them correlated `0.67`–`0.9989` with `max|z|` so
the "five-test family" was one test, `MAD` was the scale estimator under which the effect is largest,
the larger model did not replicate, and the trend was **not monotone** — the middle third scored
*below* the shallow third.

**But the withdrawal named the right object.** What was actually measured, under a word that did not
fit, is **how much of a layer's total ablation effect sits in its largest few heads**. That has a
name, it needs no percentile and no standardisation, and it is exactly scale-invariant rather than
scale-invariant-if-you-pick-the-right-denominator.

## The statistic, and why each one is chosen

```
participation_ratio   PR = (SUM|x|)^2 / (n * SUM x^2)          in [1/n, 1]; 1/n = all in one head,
                                                                1 = perfectly even
normalised PR         PRn = (n*PR - 1) / (n - 1)               in [0, 1], removes the n-dependence
                                                                that PR has by construction
gini                  Gini of |x|                              0 = even, 1 = one head
top1_share            max|x| / SUM|x|
top2_share            (two largest |x|) / SUM|x|
```

**Every one is exactly scale-invariant** — multiply a layer's effects by any constant and none of
them move. No `MAD`, no standardisation, no estimator choice. That was `R23`'s fifth defect and it
cannot recur here.

## The question, and it is NOT "does it vary"

`R23`'s attack showed the pattern is **flat across the first three quarters and steps in the fourth**.
So the interesting question is not *whether* concentration depends on depth but **what KIND of
dependence**:

| | |
|---|---|
| **World G — gradient** | concentration rises smoothly with depth. Depth is a **coordinate**, and a layer's position is readable off its concentration to within the noise. |
| **World B — boundary** | concentration is flat over most of the stack and jumps at a location. Then there is a **transition**, its position is the finding, and "deep" versus "shallow" is a discrete fact rather than a continuous one. |

**World B is what `R23`'s attack suggests, so this must be designed so confirming it is not a
foregone conclusion.** Both models are fitted and compared:

```
monotone      Spearman(depth_rank, concentration) within each (model, support) stratum
step          the best single changepoint: split the ordered layers at every position, take the
              location maximising the between-group separation
comparison    which explains more of the ordered variation, against a null in which the
              changepoint location is ALSO fitted on permuted data
```

## The strongest confound, written before the run

**A fitted changepoint always beats a fitted line on noise, because its location is a free
parameter.** Comparing them naively would return `World B` on pure noise every time.

**Control, in the same iteration:** the null refits the changepoint on **permuted** depth labels, so
the null carries exactly the same free parameter. A step wins only if it beats a step fitted to
noise.

**Second confound: `PR` depends on `n`, and the two models give `12` and `16` heads.** Controlled two
ways — `PRn` normalises the range to `[0, 1]` exactly, and **every test is run per model separately**
so an `n` difference cannot cross strata.

**Third, and it is the one `R23` failed:** pooling models let one model carry a verdict the other
contradicts. **Registered here as a hard rule: the finding must hold in BOTH models separately or it
is not a finding.** That is the discipline the discarded pre-run design of `R23` had and that its
replacement abandoned.

## Positive controls

1. **Planted gradient** — concentration rising linearly with depth. The monotone model must win.
2. **Planted step** — flat, then a jump at `0.75` depth. The step model must win.
3. **Flat** — neither fires.

All three at the real cell sizes and layer counts, asserted before the real data is read.

## Registered thresholds

Population: every layer of `qwen2.5-1.5b` (`28x12`) and `qwen2.5-3b` (`36x16`), both intervention
supports, `I_final` from `R10` and `I_all` from `R18`.

| verdict | rule |
|---|---|
| **GRADIENT** | monotone `p < 0.05` in **both** models, and the step model does not beat it |
| **BOUNDARY** | the step beats the monotone model against the refit-changepoint null, `p < 0.05`, in **both** models — and the fitted location is reported per stratum |
| **NEITHER** | no ordered structure survives in both models |
| **MIXED** | the two models disagree — **and this is reported as a failure to replicate, not as a finding** |
| **UNVERIFIED** | any positive control fails |

Reported regardless: **the full concentration profile per layer**, all five statistics, both models,
both supports — the raw material, so a reader can see the shape of the curve rather than a verdict
about it.

## What each outcome costs me

**`BOUNDARY`** is the interesting one and it is what I expect: it would say the stack has a
**transition**, and locating it is a result that does not need the word "shape" at all.

**`GRADIENT`** would mean `R23`'s non-monotonicity was an artefact of its top-order descriptors, and
that a properly scale-invariant measure sees a clean coordinate where the disguised maximum saw a
step.

**`MIXED`** — the two models disagreeing — is the outcome `R23` actually had and hid by pooling.
**Registering it as a named failure is the point.**

## Boundary

`2` models of one architecture family, `1` synthetic binding task, `1` room vocabulary, `120` items,
`1` metric, `n` of `12`–`16` heads per layer. Concentration over heads within a layer says nothing
about concentration over layers, over positions, or over any other partition. A changepoint location
fitted on `28` or `36` ordered points has wide uncertainty and no interval is claimed for it here.
