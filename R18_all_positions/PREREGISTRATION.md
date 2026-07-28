<!-- unbacked-ok: 1.25 -- the WRONG value, quoted inside the correction that records it being
 wrong. No generator emits it, and none should: emitting it would put a retracted number into
 the reference set and back it everywhere else in the repository. -->

# R18 — pre-registration: ablate at **all positions**, not just the final one

**Committed 2026-07-28, before the runner was written and before any GPU time was spent.**

## Why this run exists

[R12's verdict was downgraded to `UNVERIFIED`](../R12_cross_model/README.md) because the instrument
has a depth bias shaped exactly like the hypothesis that won.

```
every ablation in this repository:   x[0, -1, h*HD:(h+1)*HD] = 0     final position ONLY

layers that can read a head's earlier-position writes  =  NL - 1 - L
    L = 0        NL-1 downstream readers      most of the influence is UNSEEN
    L = NL-1        0 downstream readers      the measurement is COMPLETE
```

`(NL−1−L)/NL` is a **fraction of depth**. An instrument whose blind spot scales with the fraction of
network remaining downstream places its centroid at a fixed depth fraction in any model — which is
`RELATIVE`, the hypothesis R12 accepted. **The confound manufactures the winner.**

R18 removes it: `x[0, :, h*HD:(h+1)*HD] = 0`. **One line changed from R10's runner.**

## The four readings, fixed now

### 1 · Positive control on the implementation — this gates everything else

All-position ablation removes **strictly more** of head `h`'s output than final-position-only.
**The mean `|centred drop|` over the band must increase.**

> **If it does not increase, the hook did not do what it says and the run is `REFUSED`, not
> reported.** A run whose intervention is weaker than the intervention it strictly contains is not a
> measurement of anything.

### 2 · Saturation control — written before the run, because a more destructive intervention can simply break the model

Record the fraction of `(head, item)` cells whose ablated margin **flips sign**, in both arms.

> **`> 50%` sign flips under all-positions ⇒ `REFUSED`.** A saturated instrument cannot rank; drops
> measured past the point where the model no longer does the task are not comparable to drops
> measured while it does.

### 3 · The depth centroid — the reading R12 turns on

For each model, `c'` = the new rate-weighted centroid of the sham-clearing profile.

```
Δ_layers = c' − c_old
Δ_frac   = (c' − c_old) / (NL − 1)
```

| observation | verdict |
|---|---|
| `\|Δ_layers\| < 1.0` for **both** models | the bias is negligible → **R12's `RELATIVE` restored** |
| `A ≤ B/2`, where `A = \|Δ_frac₁.₅ᵦ − Δ_frac₃ᵦ\| × 35` and `B = \|Δ_layers₁.₅ᵦ − Δ_layers₃ᵦ\|` | the shift is **fraction**-shaped → the bias is a depth-fraction bias, `RELATIVE` was its shadow → **R12 `OVERTURNED`** |
| `B ≤ A/2` | the shift is **layer**-shaped → the bias is absolute, the depth-fraction reading survives → **R12 restored** |
| otherwise | **`UNRESOLVED`** — R12 stays `UNVERIFIED` |

`1.0` layer is chosen because R12's own bootstrap CI on `qwen2.5-3b` is `[21.52, 24.01]`, half-width
`1.2439` layers: a shift under one layer is inside the uncertainty the verdict already carried.

> **Corrected after commit `6e8ddac`, and the correction is a defect not a tidy-up.** This line first
> said `1.25`, computed in my head from two already-rounded endpoints instead of read from the
> bootstrap. **The `1.0`-layer threshold is untouched** — it is the commitment, and it was never a
> function of this digit. But the number citing it shipped wrong, and by [R17's own
> rule](../R17_floor_portability/) — *a pattern caught before shipping is not a defect in the
> artifact* — this one was caught **after**, so it is filed as `D86`. **The rule cuts against its
> author one step after he wrote it.**

### 4 · Does the head **ranking** survive? — and this is the kill

Spearman of `|centred drop|` over the `168` band heads, all-positions against final-position-only.
Same thresholds as [R15](../R15_shuffled_scan/PREREGISTRATION.md), for the same reason:

| | |
|---|---|
| the ranking transfers | **`≥ 0.7`** |
| the ranking does not | **`≤ 0.3`** |
| in between | report it, claim neither |

> **KILL:** if the ranking does not transfer, then *"a head"* and *"a head's write at the final
> position"* are **different objects**, and every head-level number in this repository — the ranks,
> the `1 of 8`, the `10`-of-`168`, R11's disjoint-item replication, R16's attention comparison — is
> about the latter. **That would be the largest relabelling this project has had to do**, and it is
> the outcome I expect least and would find most expensive.

Also reported, without a threshold attached: the eight published heads' ranks and `×floor` under the
new intervention.

## What R18 cannot answer

* **It does not decompose *which* earlier positions matter.** All-or-final is a two-point contrast;
  a per-position sweep is `n_positions ×` the cost and is not run here.
* **Two models.** The centroid rule needs exactly two to separate fraction from layer, and two
  points establish no law — the same limit R12 already carries.
* **A restored `RELATIVE` would still be `CONFIRMED-on-this-task`.** R13 established the task is
  fixed-position retrieval; nothing here changes that scope.

## Cost

`2 × NL × NH` forward passes per model — the same count as R10, which took **16 minutes** for
`qwen2.5-1.5b` on the RTX 5080. Two models, submitted through `pueue`, queued behind another
project's job `219`. **The GPU was not free when this was written; the previous report said it was,
and that was wrong.**
