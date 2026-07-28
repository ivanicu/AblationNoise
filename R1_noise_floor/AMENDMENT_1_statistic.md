# R1 AMENDMENT 1 — the summary statistic was badly chosen, and this is the record of changing it

Written 2026-07-27, **after two models had run and before any further model runs**, so that the
change is on the record rather than fitted to whatever comes next. The original pre-registration is
`bc3096d`; its results for those two models are `ea1da6b`. Nothing below revises a measured number.

---

## What happened

The original gate was **median band floor over the set sizes {1,2,5,10,20}**, with
`>= 0.10 -> FLOOR-IS-LARGE`, `< 0.03 -> the line dies`.

Two models ran. They disagreed on the gate:

| model | median band floor | verdict as pre-registered |
|---|---|---|
| qwen2.5-1.5b | 0.117 | FLOOR-IS-LARGE |
| qwen2.5-3b | 0.070 | AMBIGUOUS |

**That disagreement is recorded as-is and is not being revised.** But looking at the per-size rows
shows the median was pooling two regimes that behave *oppositely* across the two models:

| k | 1.5b band/sham | 3b band/sham |
|---|---|---|
| **1** | **6.6×** | **5.0×** |
| 2 | 10.8× | 1.7× |
| 5 | 1.4× | 2.4× |
| 10 | 1.4× | 3.4× |
| 20 | 1.3× | 4.1× |

At k=1 both models agree that ablating *which* head matters 5–7× more than ablating an early-layer
head at all. Above k=5 the two models diverge in **direction** — 1.5b's ratio collapses toward 1,
3b's climbs. A median over a set of numbers whose trend reverses between models is not a summary of
anything; it is an average of two different quantities.

## Why this is a change of statistic and not a change of result

The floor numbers stand. What changes is which of them the gate reads. The failure was in the
pre-registration itself: it chose an aggregate before knowing whether the thing being aggregated was
homogeneous, which is the same error as quoting a mean across a bimodal distribution.

**The honest cost of this amendment:** the original gate is now known to be answerable either way
depending on which models enter the sample, so **the two verdicts already recorded may not be
quoted as evidence for the amended gate.** They are the observation that motivated it. The amended
gate is tested only on models run after this file is committed.

## The amended statistic

**PRIMARY — `ratio_k1` = band_floor(k=1) / sham_floor(k=1).**
Does the identity of a single ablated component matter more than the fact of ablating one? k=1 is
chosen because it is the resolution at which the literature actually works — "we found the head" is
a k=1 claim — and because it is the only cell where the two models already agree, which is a
weakness of the evidence for choosing it and is stated as such.

**SECONDARY, reported never gated — `floor_k1` = 2·sd(k=1 band null) / |baseline margin|.**
The number a reader compares their own single-head effect against. On qwen2.5-1.5b it is 0.098,
i.e. any single-head effect below ~10% of the answer margin is inside the noise.

## The amended gate, on models run after this commit

```
K1-COMPONENT-CHOICE      ratio_k1 >= 3.0 in at least 3 of at least 4 valid models
                         -> the deliverable is licensed: "report a k=1 null or your single-head
                            result is unreadable", with a number per model family.

K1-NO-SPECIFICITY        ratio_k1 < 2.0 in the majority of valid models
                         -> single-component ablation noise is not about which component; the
                            line dies and R2-R10 pivot to the EM object-level results.

AMBIGUOUS                otherwise -> more model families before any claim.
```

**A "valid model" is defined before the fact**, because the phi-3.5-mini run exposed that this was
undefined: a model must answer at least 30 of the seed set correctly, or the run REFUSES and writes
no atlas cell. A refusal is a statement about the model/task pairing, not about the floor, and it
may not be counted toward either branch of the gate.

## What would still make the amended statistic wrong

`ratio_k1` compares the studied band against an early-layer sham. If a model routes this task
through *early* layers — which the sibling EM project measured for one checkpoint — the sham band
is not inert for it, the ratio collapses toward 1, and the gate would read that as "no specificity"
when the truth is "the sham was drawn from a live region". **Mitigation, added to the runner:** every
run now also reports the sham arm's own absolute floor, so a sham that is not inert is visible
rather than silently deflating the ratio. It is not a fix — it is a disclosure, and any model whose
sham floor at k=1 exceeds 0.02 is flagged rather than gated.
