# Pre-registration — can the head's write even REACH the readout? The third predictor

Written 2026-07-28, **before the statistic was computed**, committed alone so git ordering rather than
my word establishes that the thresholds preceded the numbers.

## Where this comes from

`mechanism()` (registered separately, run) left **`0.8777` of the rank ordering unexplained**.
Magnitude accounts for `0.1148`, informativeness for `0.0075`. The residual is the object.

The next candidate on that file's own list, and the only one computable without a GPU:

> **A head's write can be large and still move nothing, if it lands in a direction the readout does
> not look at.**

The readout here is a margin between four room tokens. Only the component of a head's write inside
the **room-contrast subspace** can change that margin at all; everything orthogonal to it is
invisible to this task's metric by construction.

## Why this is not the OV circuit, which is already measured

`instrument_triangle` reports `OV.rooms × ablation.I_final` at `0.0618` pooled — the direct-path OV
circuit does not predict ablation magnitude. **That is a different quantity.** OV asks *does this head
copy a room token to itself*, composing `W_V`, `W_O` and both embeddings. This asks only *does this
head's output subspace intersect the directions the margin is built from*, with no `W_V` and no
copying semantics. A head can have zero copying dominance and full readout reach.

## The statistic

For each band head `h` in `L14`–`L27` of `qwen2.5-1.5b`, from weights only:

```
u_t   = g ⊙ W_E[room_t]                 t = 1..4   (tied embeddings; g = final RMSNorm scale)
P     = orthogonal projector onto span{ u_t − mean_t(u) }        rank 3
align_h = ‖P · W_O^(h)‖_F / ‖W_O^(h)‖_F
```

`W_O^(h)` is `o_proj.weight[:, h*HD:(h+1)*HD]`, shape `(d_model, 128)`. The ratio is **scale-free by
construction**, which is the point: it separates *can this head reach the readout* from *how big is
this head*, and magnitude is already accounted for separately.

**The final RMSNorm scale `g` is included** because `D113` established that omitting it computes the
circuit in the wrong basis. Tied embeddings (`tie_word_embeddings=True`) mean `W_U = W_E`.

## The strongest confound, written before the run

**The null for this ratio is not zero.** Projecting a random `1536 × 128` subspace onto a `3`-D
subspace gives an expected Frobenius ratio of about `sqrt(3/1536) ≈ 0.0442`. A head at `0.044` has
**no** readout reach beyond chance. Comparing `align_h` against `0` would make every head look
aligned.

**Control, in the same iteration:** the random-matrix baseline is simulated, not assumed — Gaussian
`W_O` blocks of the true shape, and the observed distribution is reported against it.

**Second confound:** `align_h` may track `W_O`'s conditioning. `wo_block_conditioning` already holds
per-head `smax`, `srank`. Reported, and partialled out where it matters.

**Third confound: depth.** As in `mechanism()`, everything is computed pooled **and** within-layer,
and the within-layer version decides — pooling was measured there to *mask* rather than inflate.

## Registered thresholds

Effect = `|drop − mu_band|` from `R10_exhaustive`, the centred statistic actually used.

| verdict | rule (within-layer partial, controlling `mean_norm`) |
|---|---|
| **ALIGNMENT-MATTERS** | `partial(|eff|, align \| norm) >= 0.30` |
| **ALIGNMENT-IRRELEVANT** | `< 0.15` |
| **MIXED** | between |

And the number that actually matters, reported regardless of the verdict word:

> **the three-predictor unexplained rank fraction, against the current `0.8777`.**

`N_PERM = 20000`, depth-preserving null (shuffle effect within layer), seed `20260728`.

## Positive controls

1. **The projector is rank 3** — asserted, not assumed. Four room directions minus their mean.
2. **A planted head reaches 1 and an orthogonal head reaches the random baseline.** Construct
   `W_O` whose columns lie inside the room subspace (expect `align ≈ 1`) and one whose columns are
   drawn orthogonal to it (expect `align ≈ 0`). An instrument that cannot separate those two is not
   measuring reach.
3. **The random baseline is simulated**, and the observed heads are reported against it rather than
   against zero.

## What each outcome costs me

**If `ALIGNMENT-MATTERS`:** part of the floor's width is a fact about *geometry* — which heads can
address the readout at all — and that is a static, weight-only explanation available to anyone
without running the model.

**If `ALIGNMENT-IRRELEVANT`:** three static predictors have now failed to explain `~88%` of the
width. **That would make the case that no weight-only property explains it**, and the remaining
explanation is behavioural — compensation / self-repair — which cannot be read off the weights and
needs the co-ablation experiment this repository has never run. **That is the outcome with the larger
consequence, and it is the one I expect.**

## Boundary

One model, one metric, one task, `I_final`, `168` band heads, `n = 12` per layer. Direct path only:
no MLPs, no composition with other heads, no attention pattern — a head's write may be routed through
later layers, and this measures none of that. Correlation, not causation.
