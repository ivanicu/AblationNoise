<!-- unbacked-ok: 4.66e-07 3.18e-04 1.46e-03 1.40e-06 3.18e-07 1.40e-03 4.94
 -- HAND ARITHMETIC ON BACKED VALUES, and deliberately not emitted by a generator yet, because this file
 must be committed BEFORE the run whose tolerance it sets. Every one of them derives from three numbers the
 gate already checks -- the measured worst |delta mean| 5.103e-06, L03H01's sd_items 3.484e-03, and n = 120,
 all emitted by R29_cancellation/scan.py -- by two operations a reader can redo in their head:
   4.66e-07 = 5.103e-06 / sqrt(120)          the sem's absolute numerical floor
   3.18e-04 = 3.484e-03 / sqrt(120)          L03H01's own sem
   1.46e-03 = 4.66e-07 / 3.18e-04            that cell's relative floor
   3.18e-07 = 1e-3 * 3.18e-04                what the OLD rule allowed it, below its floor
   1.40e-06 = 3 * 4.66e-07                   the new absolute bound
   1.40e-03 = 1.40e-06 / 1e-3                the sem above which the new rule is STRICTER
 The 4.94 is L03H01's snr, printed by the same run. After the rerun the emitter carries all of them and
 this marker shrinks; whatever is still listed is still hand arithmetic. -->
# Amendment 1 — a fixed relative tolerance over a heterogeneous population is not one test

Registered 2026-07-29, after the positive control failed on 1 cell of 336, before any rerun. Committed
alone.

**This is a LOOSENING for the quiet cells and a TIGHTENING for the loud ones, and it is registered as
both.** No `Λ` has been read, which is the only circumstance under which changing a control is legitimate.

## What failed

Registered: reproduce R10's `per_head` means to `1e-5` absolute and R11's `per_head_sem` to `1e-3`
**relative**, cell by cell, or stop. The means passed at a worst `5.103e-06`. The sem failed at a worst
`2.269e-03` — in **one** cell.

```
per-cell relative sem discrepancy   median 2.585e-05   p95 2.188e-04   over tolerance 1 of 336
  L03H01  rel 2.269e-03   sd_items 3.484e-03   snr 4.94
```

Batching changed the reduction order — unbatched, R26's gate 2 reproduced `base_margin` at `|Δ| = 0.000e+00`
— and `5e-6` absolute per item is what that costs in float32. A sem is a difference of near-equal numbers,
so that absolute noise becomes a **relative** sem error scaling as `1/sd`:

```
sem precision  ≈ 5.103e-06 / √120 = 4.66e-07  absolute
L03H01 sem     = 3.484e-03 / √120 = 3.18e-04
⇒ its own relative floor           ≈ 1.46e-03
```

Its observed `2.269e-03` is about `1.6×` that floor. **A single relative bound over a population spanning
orders of magnitude in `sd` is three different tests wearing one number**, and for the quietest cells it sits
below what float32 can deliver.

## The replacement

State the sem tolerance in the units the instrument's noise actually lives in:

```
|sem_got − sem_ref|  ≤  3 × (worst measured |Δmean| over all cells) / √n
```

With the measured `5.103e-06` and `n = 120`, that is `1.40e-06` absolute margin-nats. The factor `3` is the
band on a noise scale, not a coverage: the per-item divergence is a worst case already, and a sem is a
scaled sd of those divergences, so `3×` allows for the sd of the noise exceeding its worst single element
without opening the bar to a genuine implementation error.

**The relative distribution is reported beside it** — median, p95, max, and the count over `1e-3` — so the
old rule's verdict remains visible and this amendment cannot quietly bury it.

## Why it is a tightening as well as a loosening

- **Loosened** where `sem_ref` is small: `L03H01` at `sem = 3.18e-04` had a `1e-3` relative allowance of
  `3.18e-07`, which is *below* the `4.66e-07` floor. The new absolute bound of `1.40e-06` is reachable.
- **Tightened** wherever `sem_ref > 1.40e-03`, because `1e-3` relative then allowed more than `1.40e-06`
  absolute. The scan's median sem is well above that, so **the new rule is stricter for the majority of
  cells** — it is not a blanket relaxation.
- **Still able to fail**: a wrong ablation site, a padded batch putting the query at the wrong position, or
  a `[:, -1]` slice on the wrong axis all move a sem by orders of magnitude more than `1.40e-06`. The mean
  tolerance is unchanged at `1e-5` absolute and remains the primary gate.

## What is not being changed

The three worlds, the prediction matrix, all five decision thresholds, the jackknife precision gate on
`Λ`, both confound controls, and the stopping rule are untouched. The mean-reproduction tolerance is
untouched. Only the sem tolerance's **unit** changes.

## If it fails again

Then the per-item pipeline does not reproduce the published scan within the arithmetic the scan was computed
in, `Λ` is not read, and **that is the round's result**: the published per-head numbers are not recoverable
from a batched replay, which would make every cross-round comparison in this repository conditional on the
batching of the run that produced it. Reported as exactly that, and not as a null.
