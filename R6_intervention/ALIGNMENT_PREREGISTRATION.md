<!-- unbacked-ok: 2307.15771 2402.15390 2607.01940 -- arXiv identifiers for the self-repair
 literature, not measurements; same class as the identifiers exempted at the top of README.md. -->
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

---

# Amendment 1 — the outcome

Appended 2026-07-28 after running the frozen weight extraction and `mechanism()`. Thresholds
unchanged.

## Positive controls, all three exact

| control | returned |
|---|---|
| projector rank | `3`, asserted in the extractor, not assumed |
| planted head inside the subspace | `align = 1.0000` |
| planted head orthogonal to it | `align = 0.0000` |
| simulated random baseline | `0.0440 ± 0.0016` against the analytic `sqrt(3/1536) = 0.0442` |

Perfect separation of the two planted cases, and the simulated null lands on the analytic value.
**The instrument measures what its name says.**

## The geometric fact, which is worth more than the correlation

```
observed readout reach over the 168 band heads
  min 0.0288      median 0.0440      max 0.0746
  random baseline 0.0440
  median / baseline  0.9999x          max / baseline  1.6950x
  above the null's 95th percentile: 42 of 168   (8.4 expected by chance)
```

**At the median, a band head's write is exactly as aligned with the room-contrast subspace as a
random projection would be.** The entire observed range sits inside `1.7×` of chance. There is a real
excess in the tail — `42` heads above the null's `p95` against `8.4` expected — but it is an excess of
*small* deviations, not a population of readout-addressing heads.

## Registered verdict: `MIXED`, and it does not survive multiplicity

```
within-layer partial (|centred effect|, align | mean_norm)   +0.1712   p = 0.0455   null 97.5th 0.1685
pooled                                                       +0.3249
align vs mean_norm                                           -0.0429   (nearly independent)
```

`0.1712` sits between the registered `0.15` and `0.30`, so the rule returns `MIXED`. **And it is
`0.0027` above its own null's 97.5th percentile.** This is the third predictor tested against the same
effect vector; at three tests the Bonferroni threshold is `0.0167` and the uncorrected `0.0455`
**does not clear it**. Reported as MIXED-and-not-significant-after-correction, not as a positive.

## The number that matters

```
unexplained rank variance   2 predictors  0.8777   ->   3 predictors  0.8484
```

Readout reach adds `2.9` percentage points. **Three static, weight-and-activation-derived predictors
together account for about `15%` of the ordering, and `85%` remains.**

> **No weight-only property tested here explains the width of the reference distribution.** That was
> the branch registered as *"the outcome with the larger consequence, and the one I expect"*. It is
> the outcome.

## And it kills a sentence I wrote one step earlier

`mechanism()`'s amendment says pooling **masks** rather than inflates, and used that to argue "pooled
is conservative is not a general fact". It is worse than that:

```
magnitude    pooled +0.1299   within-layer +0.3388     pooling MASKS   (2.61x)
alignment    pooled +0.3249   within-layer +0.1712     pooling INFLATES (1.8979x)
```

**The direction of the pooling bias is a property of the PREDICTOR, not of the dataset.** Same 168
heads, same effect vector, same layers — and pooling moves one predictor up and the other down by
comparable factors. So neither *"pooled inflates"* nor *"pooled masks"* can be carried as a rule; the
within-layer computation has to be done every time, and any past claim defended by *"pooling would
only have been conservative"* was defended by nothing.

## What is left, stated as the research question rather than as a gap

The residual `0.8484` is not explained by how much a head writes, how variable its write is, or
whether its write can reach the readout at all. **What remains is not a property of the head — it is
a property of what the rest of the network does when the head is gone.** That is compensation, it
cannot be read off the weights, and the experiment is co-ablation:
`2307.15771`, `2402.15390`, `2607.01940`.

## Boundary

One model, one metric, one task, `I_final`, `168` band heads, `n = 12` per layer, direct path only —
no MLPs, no composition through later attention, no attention pattern. A head's write may be read and
re-expressed by a later layer, and this measures none of that; a low direct reach does not mean a
head cannot influence the margin.
