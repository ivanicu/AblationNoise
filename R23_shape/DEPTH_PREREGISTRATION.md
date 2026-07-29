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

---

# Amendment 1 — the correlation instrument FAILED its own control, and the replacement has a MEASURED detection window

Appended 2026-07-29, **before the replacement was run on the real data**. Committed alone.

## What failed, and it is the opposite of what I registered

The registered statistic was `Spearman(depth, descriptor)` per stratum. On a planted gradient of
`df 30 -> 2` — an enormous shape change — it did not come close to firing. **It did not fire.**

**The ordered test is WEAKER here than the unordered one, not stronger**, which is the reverse of the
argument that motivated it. A correlation uses each cell individually, and a shape descriptor on
`n = 12` is too noisy to survive that; the pivot's variance statistic pools all `128` cells into one
number and keeps its power. **Registering "ordered is strictly more information" was right in
principle and wrong about this data, and the control said so before anything was read.**

A binned two-group version, comparing pooled standardised values between shallow and deep cells,
**also failed** the same plant on all four descriptors (nowhere near firing on any of them). Per-cell standardisation at
`n = 12` is itself so noisy that it erases much of the shape difference it exists to preserve.

**What did pass, cleanly, in every version: the scale-gradient control.** One shape carrying the real
measured scale gradient never fired — silent on every descriptor. **The descriptors do
not leak scale.** That confound is closed and stays closed.

## The replacement, in the instrument's own currency

The pivot already has a machine that passed both its controls: fit a **single Student-t `df`** to a
group of cells by matching the median per-cell descriptor. So compare **shallow versus deep in that
currency**:

```
statistic   median per-cell descriptor, deep group minus shallow group
null        permute the shallow/deep labels over WHOLE CELLS, preserving cell structure
            (a difference between two groups, so the mixture trap that killed the pivot's first
             three nulls does not apply -- permuting makes BOTH groups mixtures and SHRINKS the
             difference, which is the conservative direction)
```

## Its detection window is MEASURED, and reported as a limit rather than assumed away

```
df  30 -> 2     delta +0.1237   p 0.4957   BLIND
df  20 -> 2     delta +0.4436   p 0.0113   fires
df  10 -> 3     delta +0.1434   p 0.6602   BLIND
df   8 -> 3     delta +0.0013   p 0.9973   BLIND
df   6 -> 3     delta +0.1687   p 0.4630   BLIND
df   6 -> 4     delta +0.1356   p 0.7748   BLIND

planted_10_to_3        delta +0.6698   p 0.0420   fires
flat                   delta -0.3543   p 0.0786   silent
scale_gradient         delta -0.1019   p 0.6596   silent
```

**⚠ And the window is RAGGED, not a threshold.** `df 20 -> 2` fires while `30 -> 2`, `10 -> 3` and
`8 -> 3` do not, and the `10 -> 3` **control arm** fires on its own independent draw while the
**window row** for the same gradient does not. Each row is one synthetic draw at `1500` permutations,
so the window measures a **probability of detection, not a cutoff** — and at these effect sizes that
probability is near a half. **The positive control passing was therefore partly luck, and saying so
is the point: it makes the control weak evidence, not strong.** What rescues the reading below is
that the observed effect is far above that edge — `p = 0.00125` and `m_break 40.01` on the strongest
descriptor, against a plant the instrument can barely see.

**`q90|z|` is not monotone in `df` over the whole range.** At `df = 2` the cell's own `MAD` inflates
along with the tail, so the ratio saturates and a `30 -> 2` gradient reads as no change at all
(the two group medians land on top of each other). **The instrument has a WINDOW: it sees moderate shape differences and is blind
to extreme ones.** That is a property of the measurement, it is measured here rather than discovered
later, and it bounds every negative result below.

## Registered thresholds, restated for the replacement

| verdict | rule |
|---|---|
| **DEPTH-READS-SHAPE** | `>= 3` of `5` descriptors at `p < 0.05` with `m_break >= 5` |
| **NO-DEPTH-TREND-IN-WINDOW** | none reject — **and the claim is bounded by the window above**, never stated as "no trend" |
| **MIXED** | between, descriptors named with `m_break` |
| **UNVERIFIED** | the `10 -> 3` plant fails, the flat arm fires, or the scale-gradient arm fires |

**The negative verdict is renamed.** A test with a measured blind spot cannot return *"there is no
trend"*; it returns *"no trend of a size this instrument can see"*, and the size is now a number.

## Boundary added

The window is measured on Student-t gradients only; a shape change of a different kind may sit
inside or outside it and this does not say which. `m_break` is Bonferroni. Cell-level permutation
preserves cell structure but not the correlation between adjacent layers.

---

# Amendment 2 — the outcome: `DEPTH-READS-SHAPE`, and it is tail weight only

Appended 2026-07-29 after `depth.py`. **No threshold above was changed.**

## Controls

```
planted_10_to_3        delta +0.6698   p 0.0420   fires    PASS (must fire)
flat                   delta -0.3543   p 0.0786   silent   PASS (must not fire)
scale_gradient         delta -0.1019   p 0.6596   silent   PASS (must not fire)
```

The scale-gradient arm — one shape carrying the **real measured** scale gradient — is silent at
`p = 0.6596`. **The descriptors do not read scale as shape.** That was the confound that would have
made everything below meaningless, and it is closed by measurement rather than by argument.

## Shallow versus deep

```
descriptor        shallow      deep      delta         p        m_break
q90_abs_z         +3.0461   +4.2225   +1.1764   0.008248        6.06
q99_abs_z         +4.7989   +7.6995   +2.9006   0.001250       40.01
kurt_z            -0.4142   +1.1299   +1.5441   0.003499       14.29
sd_over_mad_z     +2.0714   +2.8706   +0.7992   0.004999       10.00
bowley_z          +0.0008   +0.0917   +0.0909   0.303924        0.16
```

**Four of five reject, and all four survive the five-test family** (`m_break >= 5`). Registered
verdict: **`DEPTH-READS-SHAPE`.**

## What the result actually says, at its own size

> **Deeper layers have HEAVIER-TAILED ablation-effect distributions, and only the tail moves.**

- Every rejecting descriptor is a **tail** measure — the `90`th and `99`th percentiles of the
  standardised magnitude, kurtosis, and `sd/MAD`.
- **`bowley_z`, the symmetry index, does not move** (`p = 0.3039`). The distribution does not become
  lopsided with depth; it becomes **more extreme in both directions**.
- The effect is large where it is significant: `q99|z|` goes `4.7989 -> 7.6995`, a `1.6044x` change in a
  quantity from which scale has already been removed cell by cell.

**And it is not the scale.** The scale itself moves `1.2346x` shallow to deep — `0.057048 -> 0.070430`
median `MAD` — while the tail descriptors move `1.3862x`, `1.6044x` and `1.3858x`. The shape change is
**larger than the scale change**, and the scale-gradient control shows the instrument does not
confuse them.

## The reading this licenses, and the one it does not

**Licensed:** in deep layers a few heads matter far more than a typical head, while in shallow layers
the effects are more evenly spread — and *how unevenly* is readable off the distribution's shape
without knowing which layer you are looking at. **Shape is an observable, and it carries depth.**

**Not licensed:** any mechanism. Nothing here says *why* deep layers concentrate their effect, and
attributing one would be attributing a mechanism to a datum that does not require it. That is the
next question and it is not this one.

**Not licensed either:** *"the shape varies"* as a general statement. This is **depth**, on `2`
models, `1` task, `1` metric, with `bowley` flat and `model` and `support` barely moving anything in
`R23`'s own axis table. The one axis tested is the one that moved.

## The honest weakness

**The instrument's positive control was near its own detection edge and the pass was partly luck** —
stated in Amendment 1 with the ragged window as evidence. What carries the reading is not the control
but the **margin**: the observed `q99|z|` effect has `m_break 40.01` against a plant the instrument
detects roughly half the time. **A weak control plus a large margin is a weaker result than a strong
control plus a large margin, and it is reported as the former.**

## Boundary

`2` models, `1` task, `1` vocabulary, `1` metric, `I_final` and `I_all` pooled across strata,
`n_c` of `12`–`16`, shallow `= depth < 1/3` and deep `= depth >= 2/3` with the middle third
**unused**. Cell-level permutation preserves cell structure but not the correlation between adjacent
layers, so the effective number of independent cells is smaller than the count and every `p` here is
optimistic by an unmeasured amount.
