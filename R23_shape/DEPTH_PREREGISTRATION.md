# Pre-registration — is tail weight a MONOTONE function of depth? The ordered question the pivot throws away.

Written 2026-07-29, **before the trend statistic was computed**, committed alone so git ordering
rather than my word establishes that the thresholds preceded the numbers.

## Why this and not another sweep

`R23`'s pivot asked *"are the `128` cells all the same shape"* — an **unordered** question — and
returned a bounded answer: four of five descriptors consistent with one shape, the fifth rejecting at
`p = 0.023` with `m_break 2.18`.

**The axis breakdown, reported regardless of that verdict, moved every descriptor the same way:**

```
                        depth shallow / deep
excess_kurtosis           -0.4655 / +0.2598
q99_over_q50_abs           3.6830 / 5.4502
sd_over_mad                1.8195 / 2.5218
hill_tail_index            0.4247 / 0.5036
```

Model and support move them barely and not consistently in sign. **Depth moves all four, and moves
all four toward heavier tails.** An unordered test cannot see that — it treats layer `27` and layer
`3` as two arbitrary labels. **The ordering is information the pivot discards, and using it is
strictly more powerful.**

## The two worlds

| | |
|---|---|
| **World D — depth reads off the shape** | tail weight rises monotonically with depth. Then the shape of a layer's ablation-effect distribution is a **readable channel**: it tells you where in the stack you are, without knowing. "What kind of computation does layer `L` do" acquires an observable that the width discards. |
| **World F — flat** | the four medians above are three-way noise on `n_c = 12`, the ordering carries nothing, and the shape is a property of the model-and-task rather than of position in it. Then the pivot's bounded answer is the whole story and shape is not a channel. |

## The statistic

```
per (model, support) stratum, over its layers:
    rho_s = Spearman( depth_frac , descriptor )
combined = the mean of rho_s over the 4 strata
```

Stratified rather than pooled, because the two models have different depths and pooling would let a
model difference impersonate a depth trend.

## The null, and it is the same one the pivot had to build

Cells simulated from **one** fitted Student-t at the real cell sizes, then given the **real** depth
labels, and the statistic recomputed. `20000` draws. Under `World F` a trend of this size must be
reachable by chance in that null.

## The strongest confound, written before the run — and it is the whole reason for a second control

**Depth and SCALE are already known to be confounded**: deeper layers have larger effects, which is
established in this repository. **If a descriptor is not perfectly scale-free, a scale gradient
becomes a shape gradient**, and the trend would be real, monotone, and about the wrong thing.

Two controls, both in the same iteration:

1. **Every descriptor is computed on values standardised by their own median and MAD**, so scale is
   removed by construction. Reported beside the trend: the depth trend of the **scale itself**, so a
   reader sees the two are different quantities and can compare their magnitudes.
2. **A simulated arm carrying the REAL scale gradient and exactly ONE shape.** Draw every cell from
   one Student-t, scale it by the cell's **actual** measured `MAD`, then run the whole trend test.
   **It must not fire.** If it does, the descriptors leak scale and no trend below is readable.

**A third, and it is the one I expect to bite:** a monotone trend across `28` and `36` layers is not
`128` independent points — adjacent layers are correlated. Controlled by the stratified null carrying
the same layer counts, and stated as a limit rather than removed.

## Positive controls on the instrument

1. **Planted gradient.** Cells drawn from a Student-t whose `df` falls monotonically with depth
   (`30 -> 2`), real sizes. The test **must** fire.
2. **Flat.** All cells from one `df`. The test **must not** fire.

## Registered thresholds

| verdict | rule |
|---|---|
| **DEPTH-READS-SHAPE** | `>= 3` of the `5` descriptors reject at `p < 0.05`, **and** each of those has `m_break >= 5`, so the finding survives its own five-test family |
| **NO-DEPTH-TREND** | none reject |
| **MIXED** | between — and the descriptors are named, with their `m_break` |
| **UNVERIFIED** | either positive control fails, or the scale-gradient control fires |

Reported regardless: **the per-stratum `rho`**, so a trend that exists in one model and not the other
is visible instead of averaged away; and the **depth trend of the scale**, for the comparison the
first confound control demands.

## What each outcome costs me

**`DEPTH-READS-SHAPE`** makes the shape an observable and gives this project something it can hand
someone: not *"your floor does not transport"* but *"here is what the distribution looks like, and it
tells you where you are."*

**`NO-DEPTH-TREND`** kills the only directional signal in `R23` and says the shape is a property of
the model-and-task, not of position — which would make the pivot's bounded answer the whole story
and send the next step to a different axis entirely (`k`, or the other two metrics).

## Boundary

`2` models, `1` task, `1` vocabulary, `1` metric, `n_c` of `12`–`16`, `I_final` and `I_all`. A
Spearman over `28` or `36` correlated layers is not `28` independent points; the null carries the
same counts but does not model the correlation. Nothing here claims a mechanism for a trend if one is
found — that is the next question, not this one.
