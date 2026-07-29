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

---

# Amendment 1 — the registered statistic FAILED its own power control, and the reason is the finding

Appended 2026-07-29, **before the real data was touched**. Committed alone.

## What failed

The registered statistic — mean pairwise two-sample `KS` between standardised cells, against a
**permutation** null — passed control 1 and **failed control 2**: on `64` Gaussian cells and `64`
`t(2)` cells it could not reject at all. **The instrument could not tell one shape from two.**

Two further attempts also failed, and the failures point the same way:

```
descriptor dispersion vs a permutation null      mixed case p = 0.95-1.00, and the OBSERVED
                                                 dispersion was BELOW the null
descriptor dispersion vs a within-cell BOOTSTRAP  bootstrap SE at n=12 is invalid: two descriptors
                                                 over-estimate it (F ~ 0.02-0.05), kurtosis
                                                 under-estimates it (F = 1.52 under the NULL)
```

## Why — and this is a methodological fact worth more than the statistic

> **Under the alternative, the pooled data is a MIXTURE. A mixture is heavier-tailed than either of
> its components, so cells drawn i.i.d. from the pool are MORE shape-dispersed than the true cells.**
> **Any null built from the pooled data is therefore anti-powered against exactly the alternative it
> is supposed to detect.**

Permutation, bootstrap-from-pool, and re-partition all share that defect. It is not a small-`n`
problem — it is a *wrong-null* problem, and at `n = 12` it was invisible behind the noise.

## The replacement, and its null is not the pool

```
descriptor   a SCALE-FREE shape number per cell, computed on values standardised by their own
             median and MAD:  q90|z| · q99|z| · excess kurtosis · sd/MAD · Bowley skew
statistic    the between-cell VARIANCE of that descriptor
null         ONE common shape, SIMULATED: fit a single Student-t df to the pooled data by matching
             the median per-cell descriptor, then draw n_c i.i.d. from THAT for every cell and
             recompute. The null is a single shape by construction, so a mixture cannot hide in it.
```

**Measured power of the replacement, both controls, across cell sizes — this is why it is admissible:**

```
n/cell  cells   CTRL1 one t(4), 20x scale spread   CTRL2 half Gaussian / half t(2)
    12    128   p 0.5645  PASS                     p 0.0408  PASS
    24     64   p 0.1490  PASS                     p 0.0033  PASS
    48     32   p 0.3181  PASS                     p 0.0167  PASS
    96     16   p 0.1149  PASS                     p 0.0167  PASS
   168     12   p 0.4005  PASS                     p 0.0008  PASS
   336      8   p 0.7860  PASS                     p 0.0025  PASS
```

**It works at `n = 12`, so the sweep keeps FULL LAYER RESOLUTION** — `128` cells, no coarsening, no
pooling of layers. That was in doubt when the bootstrap failed and it is not any more.

## Thresholds — unchanged in substance, restated for the new statistic

| verdict | rule |
|---|---|
| **COLLAPSE** | `p >= 0.05` on **every** descriptor |
| **NO-COLLAPSE** | `p < 0.05` on **any** descriptor, and the descriptor is named |
| **UNVERIFIED** | either synthetic control fails at the real sweep's cell sizes |

Five descriptors is five tests, so the descriptor that rejects is reported **with its `m_break`** —
the family size at which it would stop rejecting — rather than as a bare `p`.

## Boundary added

The fitted `df` is chosen from a coarse grid by matching one robust statistic; it is a **null
construction, not a claim** that the data is Student-t. Nothing below asserts a parametric family for
the real distribution — the `t` is scaffolding for a null that contains exactly one shape.

---

# Amendment 2 — the outcome. `NO-COLLAPSE` by the registered rule, on one descriptor of five that does not survive its own family.

Appended 2026-07-29 after `run.py`. **No threshold above was changed.**

## Gate controls, at the real sweep's cell sizes

```
one t(4) with a 20x scale spread   p 0.95    PASS   (must NOT reject)
half gaussian / half t(2)          p 0.001   PASS   (MUST reject)
128 cells   1824 values   sizes {12, 16}
```

**The instrument separates one shape from two at `n = 12`.** That was in doubt through three failed
designs and it is not any more.

## The pivot, one test per descriptor

```
descriptor        observed var   null median        p        fitted df   m_break
q90_abs_z             4.87999        3.55125   0.205897          2         0.24
q99_abs_z            68.1909        66.606     0.488756          2         0.10
kurt_z                3.14382        2.77263   0.288856          3         0.17
sd_over_mad_z         6.33673        1.21745   0.022989          3         2.18
bowley_z              0.104314       0.0959193 0.196902         30         0.25
```

**Registered verdict: `NO-COLLAPSE`** — the rule is *"`p < 0.05` on any descriptor"*, and
`sd_over_mad_z` rejects.

## And the verdict must be read at the size it is, not at the size the word suggests

**Four of five descriptors do not reject**, including the three most sensitive to tail weight — the
`90`th and `99`th percentiles of the standardised magnitude, and kurtosis itself. The one that
rejects does so at `p = 0.023`, and **its `m_break` is `2.18`: five descriptors is five tests, and it
stops rejecting in a family of three.**

> **So the honest statement is not "the shape varies". It is: on `128` layer-cells of `12`–`16`
> heads, the between-cell shape variation is consistent with a single common shape plus estimation
> noise on four of five descriptors, and the fifth does not survive its own multiplicity.**
> **The pivot did not settle it. It bounded it.**

## What DID move, and it is the same direction on every descriptor

`Q3` was to be reported regardless of the verdict, and it is the interesting part:

```
                        model 1.5b / 3b      support final / all      depth shallow / deep
excess_kurtosis           -0.1953/-0.0413      -0.0413/-0.1521        -0.4655 / +0.2598
q99_over_q50_abs           3.8095/ 4.6143       4.9972/ 3.9079         3.6830 / 5.4502
sd_over_mad                2.0433/ 2.1650       2.2468/ 2.0584         1.8195 / 2.5218
hill_tail_index            0.4827/ 0.4852       0.4852/ 0.4827         0.4247 / 0.5036
```

**Model and support move the descriptors barely, and not consistently in sign. DEPTH moves all four,
and moves all four the SAME WAY: deeper layers have heavier tails.**

That is a directional signal the pivot's unordered test throws away — it asks *"are the `128` cells
all the same"* while the depth reading uses the **ordering**, which is strictly more information.

**So the next step is not another sweep of widths and not a re-run of this test. It is the ordered
question: is tail weight a monotone function of depth?** A test that uses the ordering can see a
trend the unordered test cannot, and if it holds, the shape is a channel that reads out depth.

## Boundary

`2` models, `1` task, `1` vocabulary, `1` metric, `n_c` of `12`–`16`, layer-resolution cells. The
fitted `df` is a null construction and not a claim that the data is Student-t. `m_break` uses
Bonferroni and is a lower bound on robustness. `k > 1` and the other two metrics are not in this cell
of the sweep. The depth reading above is a **median comparison, not a test** — that is the next step,
and it is registered separately before it is run.
