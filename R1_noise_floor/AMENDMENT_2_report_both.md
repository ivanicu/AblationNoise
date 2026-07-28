<!-- unbacked-ok: 1.25 0.049 1.7 -- the raw-noise and floor columns of the vocabulary
 comparison, computed once for this amendment and not by any current generator. They are the
 evidence FOR the amendment's rule (report raw sd beside every floor), not results. -->

# R1 AMENDMENT 2 — the dimensionless floor moves for two reasons, and one of them is the denominator

Written 2026-07-27, after the first shared-vocabulary run and **before the remaining three models
finish**, so it is on the record rather than fitted to them. Amends the estimand's *reporting*, not
the gate. Amendment 1 is `83fae5f`.

---

## The measurement that forced it

Same model (qwen2.5-1.5b), same item count (120), same layer bands, same draws. **Only the four
answer words differ** — `pine/gold/rust/frost` versus `stone/iron/glass/water`, the vocabulary
chosen so that every model's readout scores whole words:

| | pine… | stone… | × |
|---|---|---|---|
| baseline margin (**the signal**) | 4.477 | 3.287 | **0.73** |
| sd of the k=1 null (**the raw noise**) | 0.221 | 0.275 | **1.25** |
| floor k=1 = noise/signal | 0.049 | 0.084 | **1.70** |
| sd of the k=5 null | 0.522 | 0.427 | **0.82** |
| floor k=5 | 0.117 | 0.130 | **1.11** |

**At k=5 the raw noise fell by 18% while the dimensionless floor rose by 11%.** The ratio moved in
the opposite direction to the thing it is supposed to summarise, because the denominator shrank
faster than the numerator did.

## What this means and does not mean

**It does not invalidate the estimand.** `floor = sd/|margin|` is still the right quantity for
"what fraction of the measured effect is unallocated", and it is still the only version comparable
across models whose logit scales differ.

**It does mean the ratio may never be quoted alone.** A floor that rose can mean the instrument got
noisier, or the task got harder, or both, and the three have different consequences: a noisier
instrument is a property of the ablation method, a harder task is a property of the item set. From
this run they are separable only because both numbers were kept.

**And it means a floor is not a lookup value.** Changing four English nouns moved the k=1 floor by
1.7× on a fixed model. Nobody can read a floor off a table and apply it to their own setup; they
have to measure it there. That makes the tool more necessary, not less — but it forbids the
sentence "the ablation noise floor is X" without naming the task in the same breath.

## Amended reporting, effective immediately

Every cell already stores `mean`, `sd`, `min`, `max`, `floor`, `peak_to_peak_frac`, so **no re-run
is needed** — this is a reporting rule, not a new measurement:

1. **Report `sd` in margin units alongside `floor` everywhere.** Any table, figure or sentence with
   a floor in it carries the raw sd and the baseline margin that produced it.
2. **Any cross-condition floor comparison states the margin ratio too.** "Floor rose 1.7×" is
   incomplete; "raw noise +25%, signal −27%, floor +70%" is the finding.
3. **Cross-model claims require an identical answer vocabulary.** Already enforced by the shared
   `stone/iron/glass/water` set; now it has a measured reason rather than a tidiness reason.

## The gate is unchanged

Amendment 1's gate reads `ratio_k1 = band_floor(k1)/sham_floor(k1)`, which is a ratio **of two
floors measured against the same margin**. The denominator cancels, so it is immune to exactly the
effect described here. That is a property it happened to have, not one it was designed for, and it
is stated here so the next reader does not have to re-derive it.

## Scope

One model, two vocabularies. Whether the size of this sensitivity is typical is unmeasured — the
three remaining models will each contribute one more (vocabulary-fixed) point, not a second
vocabulary, so **this amendment rests on n=1 comparison and says so.**
