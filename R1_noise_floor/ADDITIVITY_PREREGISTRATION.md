<!-- unbacked-ok: 4.209 -- the WRONG hand-computed constant, quoted verbatim inside its own
 correction so the error can be read against the emitted 4.2101. No generator emits it, which is
 exactly the point being made. -->
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
`4.2101` rather than `sqrt(20) = 4.4721`, so ignoring it would manufacture spurious compression
before any mechanism.

> **⚠ Both constants were written here as `4.209` and `4.472` — my own arithmetic, in prose, three
> paragraphs after this file says hand-computed numbers are the failure it exists to catch.** The
> generator now emits them (`additivity()['hand_constants_checked']`) and the first is `4.2101`:
> **wrong in the fourth significant digit.** Corrected above; recorded here rather than silently
> fixed, because the interesting fact is not the digit but that I did it while writing the warning. The statistic is therefore the **ratio of observed to this null**, never to `sqrt(k)`.

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

---

# Amendment 1 — the outcome, including the parts that failed

Appended 2026-07-28 after running `additivity()`. Thresholds above unchanged.

## Exclusions, applied before any verdict

| excluded | why |
|---|---|
| `llama-3.1-8b`, both arms | its ladder has **only `k=1`**, so `R_sd` is `1.000` **by construction**. Counting it would let a structural identity vote — a check that cannot fail, inside my own tally |
| `qwen2.5-1.5b-bf16`, both arms | a **precision replicate** of `qwen2.5-1.5b`, not an independent family. Counting both would double one family's vote in a four-family test |

Four families remain: `internlm2-1.8b`, `phi-3.5-mini`, `qwen2.5-1.5b`, `qwen2.5-3b`.

## `R_sd(k=20)` = observed dispersion ÷ (additivity + finite-population sampling)

```
                 band     sham
internlm2-1.8b   0.924    0.798
phi-3.5-mini     1.050    2.020
qwen2.5-1.5b     0.559    2.204
qwen2.5-3b       1.931    2.997
                 -----    -----
mean             1.116    2.005
```

## Registered verdicts

| hypothesis | rule | result |
|---|---|---|
| band **COMPRESSIVE** | `< 0.8` in ≥3 of 4 | **FAILS** — 1 of 4 |
| band **ADDITIVE** | in `[0.8, 1.2]` in ≥3 of 4 | **FAILS** — 2 of 4 → **`MIXED`** |
| sham **EXPLOSIVE** | `> 1.2` in ≥3 of 4 | **HOLDS** — 3 of 4 |
| **the frame claim** | opposite sides of `1.0`, differing by `> 0.2` | **DOES NOT FIRE** — both means are above `1.0` |
| sign test (primary) | 8 cells in their arm's predicted direction | **5 of 8, `p = 0.3633`. NOT SIGNIFICANT** |

**The primary, distribution-free statement failed, and it failed because my band prediction was
wrong.** I predicted compression and the band mean is `1.116`. The `p = 0.0039` written into the
pre-registration was the probability of *all eight*; the tail for the count actually observed is
`0.3633`. Both are printed by the handle, side by side, because reporting the first for this outcome
is a p-value answering a question that was not asked — and that is exactly what the first version of
this function did.

## The one compressive cell is confounded, and the control says so

`qwen2.5-1.5b` band is the only cell below `0.8` (`0.559`). Its `|mean(k=20)|` is **`36.6%` of the
base margin** — a third of the way to the answer flipping. **A readout ceiling is therefore NOT
excluded there**, which is the pre-registered saturation control firing against the single result
that would have supported my prediction. `internlm2-1.8b` sham, also below `0.8`, sits at `12.5%`.

## What survives

**Means compose.** `mean(k)/k` is constant across the ladder within its own standard errors in
`5 of 5` rungs for almost every cell — so the *centre* of the reference distribution extrapolates in
`k` even where the *spread* does not. That is the same centre-versus-scale split this repository
found across intervention supports, now on a different axis, and it was not predicted.

**The sham arm expands.** `3 of 4` families exceed the additive prediction by more than `1.2×`, mean
`2.005×`. Early-layer heads that individually do almost nothing produce, in groups, far more spread
than the sum of their singleton effects allows.

**The statistic's own stability, measured for free.** The precision replicate agrees to `0.010` on the
band (`0.559` vs `0.569`) and to `0.255` on the sham (`2.204` vs `1.949`). At `n = 30` draws the sham
estimate is roughly twenty-five times less stable than the band one, which is a reason to read the
sham verdict as a direction and not as a magnitude.

## The imported claim this corrects

`R12_cross_model/README.md` states that *"single-component effects are known to be badly
non-additive"*, by citation, in the **redundancy** sense — heads with near-zero singleton effect that
matter only in company. **This repository's own ladder does not support that reading of its own
data.** The means compose; the departure is in dispersion, and it runs **toward expansion**
(`1.116` band, `2.005` sham) far more often than toward the redundancy-implied compression. The
citation may well be right about other systems. It is not established here, and it was being carried
as though it were.

## Boundary

Four families, two arms, `k ≤ 20`, one task, one metric, `I_final`, `30` draws per cell, **random**
draws within a band — not any published head set. The result files store no raw draws, so every
interval here is normal-theory and understates its own width; this is why the primary statement was
chosen to be distribution-free, and why its failure is reported as a failure rather than replaced.
