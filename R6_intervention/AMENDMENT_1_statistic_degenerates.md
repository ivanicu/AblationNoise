<!-- unbacked-ok: 0.0000355 0.0000346 0.03959 560 -- (written in the table's own decimal
 notation: the number pattern does not parse 3.55e-05, so an exemption in scientific
 notation registers 3.55 and 05 and exempts neither) -- the collapsing sham sd that made ratio_k1
 divide by ~zero, transcribed from the diagnostic run that triggered this amendment. -->

# R6 AMENDMENT 1 — the pre-registered statistic divides by a quantity the new arms drive to zero

Written 2026-07-27 **after the first model and before the second finished**, and committed before any
further result was read. The models still running write every raw quantity this amendment needs, so
nothing is re-run and no choice is made with more data in hand.

---

## What the first cell showed

`qwen2.5-1.5b`, and the round-invalidating checks did their job in opposite directions:

```
CHECK 1  zero arm vs R1's checked-in ratio_k1:  4.31x vs 4.31x  -- 0.0% apart. REPRODUCES.
CHECK 2  every arm has a live positive control:  FAIL on resample (PC = 0.77 of its own band sd)
```

```
arm        band sd    sham sd    band floor   sham floor    ratio_k1     PC    PC/band sd
zero       0.27514   0.063768      0.08372    0.0194023         4.3   0.6458        2.35
mean       0.09504   0.000117      0.02892    0.0000355       815.5   0.0981        1.03
resample   0.13012   0.000114      0.03959    0.0000346      1144.3   0.1000        0.77
```

**`ratio_k1` reports 815× and 1144×, and both numbers are meaningless.** The sham arm draws from the
*early* layers, and there an on-distribution write is nearly the identity: replacing an early head's
output with its own mean across items, or with another item's value, changes the final margin by
almost nothing. The sham sd collapses **560×**, from 0.0638 to 0.00012, and `ratio_k1` divides by it.

The pre-registration fixed the statistic — which is exactly what R4's withdrawal said a
pre-registration must do — and fixed one that **is only well-conditioned for the intervention it was
written from**. Naming the estimator is necessary and not sufficient: it also has to survive the
factor under test.

Taken at face value the gate would read `median rr = 227 ≥ 3` → `ZERO-IS-THE-ARTIFACT`, and the
top-level README's first sentence would be rewritten **on a division by zero**. The round-invalidating
check is the only reason that did not happen, and it is why the runner exits non-zero rather than
writing a harvestable verdict.

## The replacement statistic

**`readability(X) = |positive control effect| / band sd(X)`** — a known, real, previously established
effect measured against the null of the same arm.

Why this one:

* **Neither term can vanish.** The numerator is the whole of one layer's heads on the mechanism's own
  layer; the denominator is the spread over 30 single-head draws in the same band. Both are computed
  under the same intervention, on the same items.
* **It is the quantity the repository is actually about.** Every round asks whether a real effect is
  readable against random component choice. `ratio_k1` was a proxy for that, chosen because R1 needed
  a dimensionless number comparable across models; here the positive control supplies the numerator
  directly, so the proxy is unnecessary.
* **It needs no new measurement.** `positive_control` and `band_sd` are already in every result file,
  including the three cells still running. This amendment therefore cannot be a choice made to fit
  data it has not seen.
* **`ratio_k1` is still reported**, per Amendment-style discipline, marked degenerate for the mean and
  resample arms with its sham sd printed beside it so a reader sees why.

## The world that was missing from the prediction matrix

The pre-registration listed three worlds. The first cell is in none of them.

| | `readability(mean, resample)` vs `readability(zero)` | status |
|---|---|---|
| W1 INTRINSIC | ≈ 1 | live |
| W2 ZEROING ARTIFACT | ≫ 1 — on-distribution ablation reads better | live |
| W3 SCALE-ONLY | ≈ 1, absolute scales differ | live |
| **W4 ZEROING IS THE MORE SENSITIVE INSTRUMENT** | **< 1** — on-distribution ablation reads *worse* | **added here** |

W4 was not in the matrix because it did not occur to me that a *gentler* intervention could lower the
signal-to-floor ratio. On the first cell it does: the positive control falls **6.6×** (0.646 → 0.098)
while the band floor falls only **2.9×** (0.275 → 0.095), so the ratio drops from 2.35 to 1.03. The
mechanism loses more than the noise does.

**Adding a world after seeing data is a real cost and it is stated rather than hidden.** W4 is
therefore **not gated on** in this round: R6's gate can return W2, or FLOOR-SURVIVES, or AMBIGUOUS,
and W4 can only be recorded as *observed on n cells, requiring its own pre-registered round*. A world
invented from the data cannot be confirmed by the data that invented it.

## The amended gate

```
ZERO-IS-THE-ARTIFACT   median readability(mean)/readability(zero) >= 3.0 across informative models
                       AND >= 2.0 on at least 3 of them
                       -> W2. The top-level README's first sentence is rewritten in the same
                          commit as the result, exactly as the pre-registration committed.

FLOOR-SURVIVES         median ratio in [0.67, 1.5] AND in [0.5, 2.0] on at least 3 models
                       -> W1 or W3. R1 stands. `af` decides which and is reported either way.

AMBIGUOUS              anything else -> report the distribution and claim neither. A median BELOW
                       0.67 lands here and is described as W4-consistent, NOT as W4 confirmed.
```

**Everything else in the pre-registration is unchanged**: the interventions, the draws, the seed, the
inclusion rule, the aggregation by median, the retraction commitment, and CHECK 1.

## What is now known regardless of how the round ends

`CHECK 1` reproduced R1's `ratio_k1` to **0.0%** on a completely rewritten measurement path — three
interventions through one hook, a capture pass, a derangement, and a different runner. R1's k=1 number
is not an artifact of its own code.
