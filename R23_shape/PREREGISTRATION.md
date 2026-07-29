# Pre-registration — ONE shape with many scales, or many shapes? The pivot.

Written 2026-07-29, **before the statistic was computed**, committed alone so git ordering rather
than my word establishes that the thresholds preceded the numbers.

## The object changes here, and that is the point

Every round in this repository has reported the **width** of the ablation-effect distribution — one
`2 sd` floor per condition — and then established that the width varies with layer, position, `k`,
metric and task. *"It is a conditional distribution, not a scalar"* is a **negative** statement, and
this project has been polishing it instead of going past it.

**The object from here is the SHAPE.**

## The pivot, and both answers are results

For each condition `c` (model × intervention support × layer) there are `n_c` ablation effects.
Standardise each by **its own** centre and scale, and ask whether the standardised values are all
draws from **one** distribution.

| | |
|---|---|
| **COLLAPSE — one shape, many scales** | the conditional distribution is a **scale family**. Then the whole conditionality reduces to a single number per condition, the shape is universal and reusable, and *"you cannot carry a floor"* becomes *"carry the shape, measure the scale"* — the project stops being a warning and becomes usable. |
| **NO COLLAPSE — the shape itself moves** | the shape carries information the width discards. Then *"what does layer `L` do"* is partly readable off the shape of its ablation-effect distribution, and shape is a **new observation channel** this literature does not use. |

Neither outcome is a non-event, which is why this is the first step rather than another sweep of
widths.

## Design

```
cells      2 models (qwen2.5-1.5b 28x12, qwen2.5-3b 36x16)
           x 2 supports (I_final from R10, I_all from R18)
           x every layer SEPARATELY, never pooled              = 128 cells, 1824 values
standardise   z = (x - median_c) / MAD_c        robust, because excess kurtosis is 7.31
statistic     mean pairwise two-sample distance between cells' standardised samples
null          permute cell labels over the pooled standardised values
```

## The strongest confound, written before the run, and it decides the null

**`MAD_c` is estimated from `n_c = 12` or `16` values, so it is noisy.** Dividing by a noisy scale
distorts each cell in a cell-specific way **even when every cell truly has the same shape** — which
would manufacture `NO COLLAPSE` out of estimation error alone.

**Control, in the same iteration:** the permutation null is built by **re-drawing cells of the same
sizes from the pooled standardised values and re-standardising each by its own median and MAD**, so
the estimation noise is present in the null exactly as it is in the observation. A null computed on
already-standardised values without re-standardising would be the wrong null and would over-reject.

**Second confound: `n_c` differs between models** (`12` vs `16`), and a two-sample distance depends
on sample size. Controlled by keeping the sizes fixed under permutation, so every null draw has the
identical size profile.

## Positive controls — an instrument that cannot separate these is not measuring shape

1. **Synthetic collapse.** `128` cells drawn from one `t(4)` with per-cell scales spanning `20x`, same
   `n_c` profile. The test **must not** reject.
2. **Synthetic non-collapse.** Half the cells Gaussian, half `t(2)`, all at the same scale. The test
   **must** reject.

Both are asserted before the real data is touched.

## Registered thresholds

| verdict | rule |
|---|---|
| **COLLAPSE** | permutation `p >= 0.05` |
| **NO-COLLAPSE** | `p < 0.05` |
| **UNVERIFIED** | either synthetic control fails |

And reported regardless of the verdict word — this is `Q1`, the shape itself, and it is the part that
survives whatever the pivot returns:

**a full shape vector per cell**, never a single number: median, MAD, IQR, skew, excess kurtosis,
quantile ratios `q90/q50` and `q99/q50` (scale-free), a symmetry index
`(q75 + q25 - 2 q50) / (q75 - q25)`, and a **tail index** from the top decile.

And if there is between-cell shape variation: **which axis carries it** — model, support, or depth —
because that is `Q3` and it is the next step either way.

## What each outcome costs me

**`COLLAPSE`** means most of this repository's conditionality reduces to one number, and the rounds
that carefully established *"it varies"* were establishing a scale, not a phenomenon.

**`NO-COLLAPSE`** means the width was always the wrong summary, and every floor ever quoted here
discarded the informative part of the object.

## Boundary

`2` models, `1` task, `1` vocabulary, `1` metric (`signed_margin_drop`), `n_c` of `12`–`16`. A tail
index on `12` points is a weak estimate and is reported with that stated; the **collapse** test does
not depend on it. `k > 1` and the other two metrics are not in this cell of the sweep and are the
next axes, not a claim.
