# R10 — every head, once, no sampling, in the vocabulary the published effects were measured in

[R9](../R9_depth_profile/) found that a model's quietest and noisiest layer differ by **8.1× to
96.2×** in how much a single head's ablation moves the answer. So the floor R1 compares an effect
against — **thirty draws pooled across fourteen layers** — mixes *which head you picked* with
*which layer you picked*.

> The earlier wording here said *"neighbouring layers differ tenfold"*. That is the **wrong scope**
> for the number: the largest **adjacent**-layer jump is `4.8×`, `4.9×`, `5.1×` and `15.2×` on the
> four models, and the one that clears ten is `L0→L1` — the embedding boundary, not a mid-stack
> neighbour. Tenfold is a whole-stack fact. It is corrected rather than deleted because the
> conclusion below never needed the stronger version.

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

> ### The band-pooled floor in that table is a THIRTY-DRAW ESTIMATE, and this round contains the exhaustive one
>
> `0.4418` is `2 × sd` of **30 random draws** from a band of **168** heads. R10 measured all 168.
> Nobody had put the two side by side, so the reference class for the repository's headline was
> never itself checked. `make headline` now recomputes it — the 30 draws are replayed from
> `draw_seed 20260727` and looked up in this round's exhaustive table, returning the recorded sd
> with a **reconstruction error of exactly `0`**.
>
> ```
> sampled floor, 30 draws            0.4418
> EXHAUSTIVE floor, all 168 heads    0.4870      10.2% higher
> what a 30-draw floor looks like    p05 0.2595   median 0.4604   p95 0.6967   =  2.7x
> ```
>
> **The sampled floor is not wrong and it is not lucky** — it sits at the `45.1`st percentile of
> its own sampling distribution. It is *unresolved*: a `2.7×` interval cannot distinguish `0.4418`
> from `0.4870`. The floor had a noise floor, which is this repository's own thesis pointed at its
> own instrument.
>
> **Against the exhaustive floor the count is `8 of 8`.** `L16H3` — the one effect that cleared,
> by `5.7%` — sits at `0.96×` and is inside. The pooled column above is kept as measured, and the
> exhaustive floor is the one the front page now uses.
>
> **And two of the eight are inside the null that judges them.** `L16H3` and `L19H0` are among the
> thirty draws; `L16H3` is that sample's **extreme value**. That is circularity, and its control is
> in `make headline`: with both removed the floor **shrinks** to `0.4131`, so `L16H3` clears by
> *more* (`1.13×` rather than `1.06×`) and the count is unchanged. **The direction is conservative,
> which does not make it acceptable** — it makes it a defect that happened to point the safe way.

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
