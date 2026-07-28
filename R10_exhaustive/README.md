# R10 — every head, once, no sampling, in the vocabulary the published effects were measured in

[R9](../R9_depth_profile/) found that neighbouring layers differ **tenfold** in how much a single
head's ablation moves the answer. So the floor R1 compares an effect against — **thirty draws
pooled across fourteen layers** — mixes *which head you picked* with *which layer you picked*.

The repository's most striking sentence depends on that floor: *the independently proven copy head
`L22H7` moves the margin by −0.132 against a floor of 0.442, so even it is inside the noise.*

```bash
python3 R10_exhaustive/run.py --model <hf-path> --tag <name>
```

---

## The design, and why it has no sampling error at all

At k=1 inside a single layer **there is nothing to sample** — there are only `NH` heads. Thirty
draws would be sampling *with replacement from twelve objects*, and the spread would be dominated
by repeats. **So every head is ablated once.** `NL × NH` measurements, exact.

That was written into the pre-registration as the control that *removes* the confound rather than
measuring it. It also strips R9's sampling noise out of the depth curve, so this round **subsumes**
R9 rather than sitting beside it.

**Original vocabulary**, because that is where the eight published effects live and Amendment 2
established the floor moves 1.7× when the four answer nouns change. R9 ran the shared vocabulary,
so R9's curve could not be used for this test however convenient that would have been.

## The result — and it went against the hypothesis that motivated the round

`L22`, the copy head's own layer, all twelve heads, `qwen2.5-1.5b`, n=120:

```
h 5  +0.3977     h 2  +0.2049     h 4  -0.0688     h 9  -0.0199
h 0  -0.3379     h 7  -0.1317 ←   h 8  -0.0260     h 6  +0.0194
h 3  -0.2214     h 1  +0.0751     h11  -0.0256     h10  +0.0099

L22's own floor (2 sd over its twelve heads)   0.3775
the band-pooled floor R1 used                  0.4418
```

**The layer-specific floor is 15% smaller, not 5–10× smaller.** `L22H7` sits at **0.35×** of its own
layer's floor and **0.30×** of the pooled one — inside both. `W_LAYERWISE` is refused; the pooled
floor was not the reason the copy head was invisible.

### And the sharper test makes the headline stronger, not weaker

Placing each of [the eight published effects](../R1_noise_floor/results/prior_effects/) against
**its own layer's** exhaustive floor:

```
head       drop    layer 2sd   × own   × pooled
L16H3   -0.4668      0.5189     0.90     1.06     inside own / CLEARS pooled
L17H0   +0.1336      0.2466     0.54     0.30
L22H7   -0.1317      0.3775     0.35     0.30
L18H9   +0.0410      0.7658     0.05     0.09
L17H11  +0.0379      0.2466     0.15     0.09
L19H5   +0.0373      0.7890     0.05     0.08
L17H7   -0.0352      0.2466     0.14     0.08
L19H0   +0.0154      0.7890     0.02     0.03

inside their OWN layer's floor :  8 of 8
inside the band-pooled floor   :  7 of 8
```

**The round was designed expecting the layer-specific floor to rescue some effects. It kills the
last survivor instead.** `L16H3` clears the pooled floor by 6% and sits at 0.90× of `L16`'s own —
`L16` is simply a noisy layer.

The two floors answer different questions and the claim survives under both:

| reference class | the question it answers | result |
|---|---|---|
| the whole band | *is this head special among the heads I might have picked?* | **7 of 8 inside** |
| the head's own layer | *is this head special among its own layer's heads?* | **8 of 8 inside** |

## What this round does NOT conclude

**Its own gate is refused.** `run.py` prints `BAND-IS-EXCEPTIONAL` at `rho +0.856`, excess `5.93×` —
computed by extrapolating the sham half's trend to the band's depth, which
[R9 established is an unfit estimator](../R9_depth_profile/): the band is the upper half of the
stack, so the only data at the band's depth *is* the band, and every "predict the band from the
rest" is extrapolation. The linear form returns negative standard deviations; the log form returned
`0.01×` and `113×` for the same quantity on other models. **Taking the verdict from the one cell
where a broken instrument looks reasonable is what it exists to prevent.**

The **curve** needs no fit and is sampling-free, and that is what this round delivers.

**One model.** `qwen2.5-1.5b`, one layer band, one task, the original vocabulary. Every number
above is exact for that cell and says nothing about the other three families.
