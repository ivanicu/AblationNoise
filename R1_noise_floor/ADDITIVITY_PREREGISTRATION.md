# Pre-registration — does the single-head reference distribution predict the multi-head one?

Written 2026-07-28, **before the statistic was computed**, committed alone so git ordering rather than
my word establishes that the thresholds preceded the numbers.

## Why this is the load-bearing claim and not another floor question

Every verdict in this repository is *"is this head unusual among heads"*, evaluated against a
distribution of **single**-component knockouts. That frame presupposes the single-head effect is a
meaningful per-component attribute — something that composes. **The repository has never tested
this.** `R12_cross_model/README.md:88` asserts single-component effects "are known to be badly
non-additive" **by citation**, and `R19_crossed_position_support/PREREGISTRATION.md:156` lists
additivity as an open question. Neither measured it.

**The data to measure it has been frozen since R1** and was never analysed: `k ∈ {1, 2, 5, 10, 20}`,
band **and** sham, `30` draws per cell, four model families. Nothing in `headline.py` reads `band_k2`,
`band_k10` or `band_k20`.

## The two worlds

| | |
|---|---|
| **World A — the unit composes** | a head's effect is an attribute of the head. A `k`-head knockout is the sum of `k` such attributes, so the multi-head distribution is determined by the single-head one plus sampling. |
| **World B — the unit is a slice** | the `k`-head response is not determined by the single-head distribution. Then "the reference distribution over components" describes one slice of the ablation response and does not extrapolate, and the repository's frame is a **choice**, not a property of the model. |

## The null is additivity **plus finite-population sampling**, not plain `sqrt(k)`

This is the strongest confound and it is being built into the null rather than mentioned afterwards.
Draws take `k` heads **without replacement** from a fixed population of `N` band heads, so under pure
additivity:

```
mean(k)  =  k * mu_pop                                  exactly, for any k
sd(k)    =  sd(1) * sqrt( k * (N - k) / (N - 1) )       finite-population correction
```

`N = 168` for the band (`L14-27` x 12) and `N = 96` for the sham (`L0-7` x 12) — **read off each
file's own `band` / `sham_band` fields, not assumed.** At `k = 20` the correction alone predicts
`4.209` rather than `sqrt(20) = 4.472`, so ignoring it would manufacture `6%` of spurious
compression. The statistic is therefore the **ratio of observed to this null**, never to `sqrt(k)`.

## Statistics and registered thresholds

For each (model, arm):

```
R_sd(k)    = sd(k)_observed   /  sd(k)_null            1.0 under World A
R_mean(k)  = mean(k)_observed / ( k * mean(1) )        1.0 under World A, but see below
```

**`R_mean` will NOT be used for any verdict.** `mean(1)` is estimated from `30` draws and its own
standard error is of the same order as itself, so a ratio against it is an uncertainty compared
against a differently-paired uncertainty — the first entry on this repository's overshoot list.
Instead the mean is tested as **constancy of `mean(k)/k` across the ladder**, each with its own
`sd(k)/(k*sqrt(30))` standard error, and reported as an interval overlap rather than a ratio.

| verdict | rule |
|---|---|
| **COMPRESSIVE** (band) | `R_sd(20) < 0.8` in **at least 3 of 4** models |
| **EXPLOSIVE** (sham) | `R_sd(20) > 1.2` in **at least 3 of 4** models |
| **ADDITIVE** | `R_sd(20)` within `[0.8, 1.2]` in at least 3 of 4 models, for that arm |
| **the frame claim** | if band and sham land on **opposite sides** of `1.0` and differ by more than `0.2`, the single-head distribution does **not** determine the multi-head response, and the front page must say so |

Distribution-free joint test: the eight cells (4 models x 2 arms) each get a direction. Under a null
of random direction the probability that all eight fall in their arm's predicted direction is
`(1/2)^8 = 0.0039`. **This is the primary inferential statement** and it needs no distributional
assumption.

## Positive controls

1. **The null must reproduce `k = 1` exactly.** `R_sd(1) = 1.000` by construction; if it does not, the
   fit is wrong and nothing else is readable.
2. **The instrument has returned non-zero**: `sd` at every `k` is strictly positive and reported in
   margin units, not only as a ratio.
3. **Saturation control, in the same iteration.** The margin flips at zero, so a compressive band
   could be a readout ceiling rather than redundancy. `mean(k=20) / base_margin` is reported for
   every model. **If it is small, a ceiling cannot be the explanation** — and the sham arm going the
   *opposite* way is a second, structural control, because a ceiling cannot produce expansion.

## Uncertainty, and its honest boundary

The result files store only `mean`, `sd`, `min`, `max`, `n_draws` — **not the 30 raw draws.** So no
non-parametric bootstrap is possible. Intervals below use the normal-theory
`SE(log sd) ~ 1/sqrt(2(n-1)) = 0.1313`. The recorded `min`/`max` show clear skew, so **for
heavy-tailed draws this understates the width**, and every interval here is therefore a **lower
bound** on its true size. It is stated rather than smoothed, and it is why the primary statement is
the distribution-free sign test.

## What each outcome costs me

**If ADDITIVE:** the repository's unit of analysis is vindicated, the citation in `R12` is wrong for
this system, and the frame stops being an assumption.

**If the frame claim fires:** every "is this head unusual" verdict in this repository is a statement
about one slice of the ablation response, and the front page's central object narrows from *the*
reference distribution to *the k=1* reference distribution. That is unwelcome and it is why this step
was chosen.

## Boundary

Four model families, two arms, `k <= 20`, one task, one metric, `I_final` only, `30` draws per cell,
random draws within a band — **not** the specific head sets anyone published.
