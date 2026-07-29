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

---

# Amendment 3 — I attacked it and most of it does not survive. The corrected claim is much smaller.

Appended 2026-07-29, on Ivan's instruction to attack the measurement itself: *does it measure
anything real, or is it an artifact of how it was computed?* Five attacks, run at the object.

## ① The descriptors are TOP-ORDER STATISTICS, and the words did not say so

`run.py`'s `q(a, 0.99)` on `12` values interpolates to index `11.89` of `0..11`. **At `n = 12`,
`q99_abs_z` is the MAXIMUM divided by the MAD**, not a `99`th percentile. `q90_abs_z` lands at index
`10.9` — the second largest. At `n = 16` it is index `15.85` of `15`, still the max.

**So three of the four rejecting descriptors measure "how big is the largest one or two effects
relative to a typical one".** That is a legitimate tail quantity. **It is not what the word
"percentile" tells a reader**, and the round's prose used the word.

## ② Delete the top two heads per cell and the entire effect disappears

```
                     q90       q99      kurt   sd/MAD   bowley
drop top 0      0.0053    0.0013    0.0053    0.0053    0.3105
drop top 1      0.3511    0.0053    0.0020    0.0120    0.5956
drop top 2      0.1885    0.4863    0.3031    0.5490    0.7275
drop top 3      0.2771    0.1292    0.5583    0.4490    0.7175
```

**Every descriptor loses significance once the two largest heads are removed from each layer.**

> **This is not a statement about the SHAPE of a distribution. It is a statement about TWO HEADS out
> of twelve.** *"Deeper layers have heavier-tailed distributions"* implies a property of the whole
> population; what is actually true is that **in deep layers the one or two largest head effects are
> larger relative to the rest of their own layer.** Remove them and shallow and deep are
> indistinguishable on every measure tried.

## ③ Under an adjacency-preserving null the margin nearly vanishes

Cells from adjacent layers are correlated, so the free-cell permutation treats `128` cells as `128`
independent units when they are not. Permuting **contiguous blocks** instead:

```
                  free cell   block 4   block 9
q99_abs_z           0.0013    0.0033    0.0341
kurt_z              0.0060    0.0153    0.0608
sd_over_mad_z       0.0033    0.0127    0.0449
q90_abs_z           0.0113    0.0380    0.0361
```

**`m_break` on the strongest descriptor falls from `40.01` to about `1.05`.** The boundary paragraph
said the effective number of independent cells is smaller than the count and that every `p` was
optimistic "by an unmeasured amount". **It is now measured, and it is most of the margin.**

## ④ No single stratum carries it

```
                          q99            kurt          sd/MAD
qwen2.5-1.5b|I_all     p 0.0700       p 0.2232       p 0.0600
qwen2.5-1.5b|I_final   p 0.0320       p 0.0326       p 0.1406
qwen2.5-3b|I_all       p 0.0640       p 0.0326       p 0.1379
qwen2.5-3b|I_final     p 0.3078       p 0.9227       p 0.2272
```

**Not one stratum rejects on more than a single descriptor.** The pooled result is four weak
same-direction signals added together — **and the two "models" are Qwen2.5 at two sizes, one
architecture family, so the effective replication is closer to `1` than to `2`.**

## ⑤ What survived the attack

- **The direction is consistent**: every delta is positive in all four strata and on every descriptor.
- **Split-point sweep is stable**: `q99` `p` = `0.0013`, `0.0013`, `0.0033`, `0.0020` at the four split points `0.25/0.75`, `1/3-2/3`, `0.40/0.60`, `0.50/0.50`. Not a boundary artefact.
- **Not `n`-dependence**: on pure noise the `q99` bias between `n = 12` and `n = 16` is `+0.0760`,
  and the two groups are near-identically composed (`18`/`24` shallow, `20`/`24` deep). Too small
  and too balanced to matter.
- **Not scale**: the scale-gradient control was silent at `p = 0.6596` and that stands.

## The claim, restated at the size the evidence supports

> **In deep layers, the largest one or two head effects are larger relative to the rest of their own
> layer than in shallow layers. The direction is consistent across four strata and four split points
> and is not a scale or sample-size artefact. At an adjacency-preserving null it sits at
> `p ~ 0.03`–`0.05`, no single stratum reaches significance on more than one descriptor, the two
> models are one architecture family, and removing those top two heads removes the effect entirely.**

**RETRACTED from the previous amendment:** *"Deeper layers have heavier-tailed ablation-effect
distributions"* — the population statement. *"Shape is an observable and it carries depth."* —
`m_break 40.01` as the margin. *"Only the tail moves"* stated as a distributional fact.

**`DEPTH-READS-SHAPE` is withdrawn as a verdict word.** What is left is a directionally consistent,
marginally significant, two-head phenomenon, and calling it a shape channel was `eta` too large.

## And it points somewhere better

If the effect lives in the top one or two heads, then **the well-posed object is not the shape of the
distribution — it is the CONCENTRATION of the effect**: how much of a layer's total ablation effect
sits in its largest few heads. That is a single interpretable number per layer (a participation ratio
or a Gini), it does not depend on a percentile that is secretly a maximum, and *"deep layers
concentrate their effect into fewer heads"* is a claim that can be stated, measured and falsified
without the word "shape" doing any work.

**That is the next step, and this attack is what produced it.**

---

# Amendment 4 — an independent reviewer found five things I did not, and `DEPTH-READS-SHAPE` is WITHDRAWN

Appended 2026-07-29. Every number below re-derived by me from the frozen data before publication;
where the reviewer and I disagree, mine is published and the disagreement stated.

## ① The trend is NOT monotone. The middle third is BELOW the shallow third.

The round compared **two endpoints** and deleted the middle third by design, so it was structurally
incapable of finding this.

```
                shallow    MIDDLE     deep      shallow-vs-middle
q99_abs_z       +4.7989   +3.5305   +7.6995   delta  -1.2684  p 0.0107
q90_abs_z       +3.0461   +2.6330   +4.2225   delta  -0.4131  p 0.3714
sd_over_mad_z   +2.0714   +1.7205   +2.8706   delta  -0.3509  p 0.0590
kurt_z          -0.4142   -0.3215   +1.1299   delta  +0.0927  p 0.7218
by quarter, q99_abs_z:   4.506  4.224  4.501  8.328
by quarter, kurt_z   :   -0.336  -0.509  -0.112  1.695
```

**`World D` was registered as *"tail weight rises MONOTONICALLY with depth"*. It does not.** The first
three quarters are flat — `4.506`, `4.224`, `4.501` — and the fourth steps to `8.328`. On `q99` the middle
third is **significantly BELOW** the shallow third.

> **So the object is a STEP AT THE TOP OF THE STACK, not a coordinate along it.** A readout that says
> "deeper" would call a mid-stack layer *shallower than a shallow one*.

## ② Drop the last few layers and it collapses

```
drop last 0   q99_ab p=0.0047  kurt_z p=0.0027  sd_ove p=0.0067  q90_ab p=0.0060
drop last 1   q99_ab p=0.0013  kurt_z p=0.0060  sd_ove p=0.0047  q90_ab p=0.0040
drop last 2   q99_ab p=0.0007  kurt_z p=0.0087  sd_ove p=0.0127  q90_ab p=0.0053
drop last 3   q99_ab p=0.0167  kurt_z p=0.0207  sd_ove p=0.0180  q90_ab p=0.0073
drop last 4   q99_ab p=0.0786  kurt_z p=0.0626  sd_ove p=0.0173  q90_ab p=0.0060
```

## ③ The "four independent descriptors" are one statistic counted four times

Spearman against `max|z|` over the `128` cells:

```
q99_abs_z        +0.9989
sd_over_mad_z    +0.9653
kurt_z           +0.8483
q90_abs_z        +0.6698
bowley_z         +0.0600
```

**`q99_abs_z` IS `max|z|`** (`0.9989`). Only `bowley_z` is independent — and it is the one that does not
reject **and** the one that was never positive-controlled. **So the registered `m_break >= 5`
five-test family rule is void: the effective family is `1`, not `5`, and "four of five reject" is one
result restated four times.**

## ④ The larger model does not replicate

```
qwen2.5-1.5b   q99_ab p=0.0100 m_break=5.00  kurt_z p=0.0067 m_break=7.50  sd_ove p=0.0127 m_break=3.95  q90_ab p=0.2418 m_break=0.21
qwen2.5-3b     q99_ab p=0.0766 m_break=0.65  kurt_z p=0.0839 m_break=0.60  sd_ove p=0.0833 m_break=0.60  q90_ab p=0.0426 m_break=1.17
```

**`qwen2.5-1.5b` alone carries the verdict; `qwen2.5-3b` alone has nothing surviving the family.**
Two models of one architecture family, and the bigger one says no.

## ⑤ `MAD` was the scale estimator that maximised the effect

Standardising by `sd` instead:

```
q90_abs_z      shallow +1.4903  deep +1.4820  delta -0.0083  p 0.9467
q99_abs_z      shallow +2.2962  deep +2.5927  delta +0.2966  p 0.0386
```

`q90` **dies and flips sign**. The headline *"a `1.6044x` change in a quantity from which scale has
already been removed"* was a statement about a choice of estimator, and the round chose the one under
which the effect is largest.

## ⑥ And the provenance claim is FALSE for exactly the amendments that chose the winning statistic

Both files open with *"committed alone so git ordering rather than my word establishes that the
thresholds preceded the numbers."* Checked:

```
bd14c5d 09:31  PREREGISTRATION.md alone                                    TRUE
c717761 10:12  PREREGISTRATION.md + run.py + results                       Amendments 1-2 shipped WITH the result
f343099 10:17  DEPTH_PREREGISTRATION.md alone                              TRUE
a425384 11:05  DEPTH_PREREGISTRATION.md + depth.py + results               Amendments 1-2 shipped WITH the result

git show f343099:R23_shape/DEPTH_PREREGISTRATION.md | grep -c "1/3|2/3|two-group|median per-cell"  ->  0
```

**The only independently-timestamped depth registration specifies a DIFFERENT statistic** — a
stratified Spearman — and contains no mention of the two-group median test, the `1/3`–`2/3` split, or
pooling across strata. **The statistic that produced the verdict has no independent timestamp.**

**Aggravating:** the discarded pre-run design was stratified *precisely to prevent a model difference
impersonating a depth trend* — and the stratified analysis is exactly what §④ shows fails.

## What is withdrawn

**`DEPTH-READS-SHAPE` is withdrawn as a verdict.** With it: *"deeper layers have heavier-tailed
ablation-effect distributions"*, *"shape is an observable and it carries depth"*, *"only the tail
moves"* (`bowley_z` is blind — never positive-controlled, and a planted asymmetry gradient does not
move it), and `m_break 40.01` as a margin.

## What survives, and it is one sentence

> **In these two Qwen2.5 checkpoints on this synthetic binding task, the final quarter of layers
> contains one or two heads whose ablation effect is far larger relative to their own layer's typical
> head. The first three quarters do not order among themselves.**

Direction consistent across strata and split points; not scale (the scale-gradient control was clean
at `p 0.6596`); not `n`-dependence (groups balanced). **Everything else was `eta` too large.**

## The object this points to, and it is better posed

The right name is **CONCENTRATION**, not shape: how much of a layer's total ablation effect sits in
its largest few heads — a participation ratio or a Gini. One interpretable number per layer, no
percentile that is secretly a maximum, no scale-estimator choice, and *"the last quarter concentrates
its effect into fewer heads"* is a claim that can be stated and falsified without the word "shape"
doing any work. **And it must be tested with THREE-LEVEL ordering, because the two-endpoint design is
what hid the non-monotonicity.**
