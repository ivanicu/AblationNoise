# R26 — what GENERATES the effect distribution: a variance budget in nats²

Registered 2026-07-29, before the checkpoints finished downloading and before any line of R26 code
existed. Committed alone.

**The thresholds, the worlds, the controls and the stopping rule in this file were chosen by an
independent clean-context navigator, not by the author of the code that will be judged against
them.** That is recorded because whose number it is decides what the number is worth: three of the
author's own thresholds in R24 were later measured to be unfalsifiable or coin-flips, and the one
defect nobody but an outside reader found was a two-character edit disabling a registered halt.

## Why this and not more of R24

R24's line is closed, and not because a result came back wrong. The bound is arithmetic: its
statistic is a dispersion estimated from `12` or `16` numbers, whose sampling `sd` is `38%` to `67%`
of the between-layer `sd` it was used to explain; `64%` to `79%` of the layers it profiled sit inside
the structureless null; and `PR = 1/(n(1+CV²))`, so all five "scale-invariant" statistics were one
reparameterisation of the same within-layer dispersion. No amendment fixes `n` = the checkpoint's
head count.

What has never been asked, in twenty-five rounds: **why the per-head effect is a distribution at
all.** Its width is `σ(log|I|) ≈ 1.10` to `1.29` nats and is the same in both checkpoints and under
both supports to within `8%`. Nothing explains that. One world is already dead — static weight size
accounts for `3.4%` of `Var(log|I|)`, and within a layer `rho(log s_max, log|I_final|) = -0.023`
against a null `sd` of `0.302`. A head's weight size does not predict its ablation effect.

## The measurement

One hooked forward pass per prompt over the existing `120` prompts, both checkpoints. **No
ablations.** At each layer's `o_proj` pre-hook, capture the concatenated per-head attention output
`z`. For every `(layer ℓ, head h)` at the query position:

```
o_{ℓ,h}     = W_O[:, h·HD : (h+1)·HD] · z_{ℓ,h}          the vector the head writes
size_{ℓ,h}  = log ‖o_{ℓ,h}‖                               nats
align_{ℓ,h} = log |⟨ô_{ℓ,h}, Δû_ℓ⟩|                        nats
Δu_ℓ        = unembed[room_correct] − unembed[room_best_other], pulled back through the final LN
```

Deliverable, one row per `(model, support, layer)`:

```
Var(log|I|) = Var(size) + Var(align) + 2·Cov(size, align)          all in nats²
```

reported with `σ` in nats. **A budget with a unit that adds, comparable across layers, supports,
models and any future checkpoint. No verdict word.**

## Live worlds

- **A — SIZE.** The effect distribution is the head-output-norm distribution. Heads differ in how
  much they write. Ontology: effect is a magnitude; "important head" means "loud head."
- **B — DIRECTION.** Norms are comparable; what differs is alignment with the readout direction.
  Ontology: effect is a geometric relation between a head's write and the decision axis, and a loud
  head can be causally irrelevant.
- **C — NEITHER.** `log|I|` is not a sum of these two logs. The effect is routed through downstream
  layers, so a first-order size × direction account of the intervention is the wrong ontology and the
  object must be re-modelled as propagation, not as a per-head property.

## Prediction matrix — read as vectors, never row by row

`ρ̄` is the mean within-layer Spearman over `28` / `36` layers.

| | `Var(size)/Var(log\|I\|)` | `Var(align)/Var(log\|I\|)` | `ρ̄(size, log\|I\|)` | `ρ̄(align, log\|I\|)` |
|---|---|---|---|---|
| **A SIZE** | `≥ 0.50` | `< 0.30` | `≥ 0.50` | `< 0.30` |
| **B DIRECTION** | `< 0.30` | `≥ 0.50` | `< 0.30` | `≥ 0.50` |
| **C NEITHER** | `< 0.30` | `< 0.30` | `< 0.30` | `< 0.30` |

The three rows are distinct vectors. The shares sum to `1` with the covariance term, so A and B
cannot both fire unless `Cov` is strongly negative — in which case the answer is **C with
cancellation** and is reported as such. There is no `or` anywhere in this rule.

## Why each threshold can fail in both directions

- **`0.50` variance share.** Not the nominal coverage of anything. The null for "this term carries
  nothing" is `0`, and the instrument has already demonstrated it can return a near-zero share — the
  static weight arm returned `0.034`. Because the three shares sum to `1`, the all-below-`0.30` cell
  is genuinely open rather than a residual category.
- **`ρ̄ ≥ 0.50` / `< 0.30`.** At `n=12` a single layer's `0.50` is only `1.7σ` from null, which is
  why the threshold is on the **mean over all layers**: null `sd` `0.302/√28 = 0.057`, so `0.50` is
  `8.8σ` and `0.30` is `5.3σ`. Both attainable, neither at a coin-flip point. No attenuation ceiling
  applies — `‖o‖` and the alignment are read off a deterministic forward pass, not estimated from
  `12` noisy points.
- **Decided on `≥ 3` of `4` cells** (model × support), never pooled. The `4` cells are explicitly
  labelled **non-independent**: `I_all` equals `I_final` exactly at the last layer of both models
  (`max|Δ| = 0.0`, mechanically necessary), and their divergence is monotone in depth
  (`rho = -0.904` / `-0.662`). The last layer is excluded from any "both supports" count because the
  two supports are provably identical there.

## The KV column — a consistency check with teeth

The grouped-query partition explains `η²` of `0.1808` / `0.1317` / `0.1324` / `0.1437` on `|effect|`
against an algebraic null expectation of `(k-1)/(n-1)`. That signal must be **carried** by one of the
two terms. Compute `η²_KV` on `size` and on `align` per layer, same groups (`h//6`, `h//8`).

| | `η²_KV(size)` | `η²_KV(align)` |
|---|---|---|
| **A SIZE** | `≥` the observed `η²_KV(log\|I\|)` | `≈` null |
| **B DIRECTION** | `≈` null | `≥` observed |
| **C NEITHER** | `≈` null | `≈` null, while `η²_KV(log\|I\|)` stays elevated → the architectural signal enters through propagation, not through the write |

"Carried" = the term's `η²_KV` within `0.05` of `η²_KV(log|I|)` in `≥ 3` of `4` cells. "`≈` null" =
within `2` permutation-null `sd`s of `(k-1)/(n-1)`. Neither bound is at a nominal coverage and both
directions are reachable — `η²` already ranges from null-level on signed effects to `2×` null on
magnitudes. **A decomposition claiming world A while leaving the KV signal unexplained in both terms
is internally contradicted, and that outcome is C-evidence, not something to smooth over.**

## Controls, in this order, and no number is read after a failed gate

1. **Weight-level identity.** Recompute `smax` / `smin` / `cond` / `srank` for all `168` `W_O` band
   blocks of the `1.5b` checkpoint and match
   `R6_intervention/results/wo_block_conditioning_qwen2.5-1.5b.json` to `6` significant figures. That
   file was frozen from the July artifacts, so this verifies the **downloaded tensor bytes** against
   a reference independent of tokenizer and prompt. Mismatch → the checkpoint on HuggingFace is not
   the checkpoint the scans measured → **stop, read nothing, report the revision hashes.**
2. **Behavioural identity.** Reproduce `base_margin` to `4` decimals through the existing
   `R10_exhaustive/run.py` prompt path: `4.476822` for `1.5b`, `6.637212` for `3b`. The `3b`
   checkpoint has no frozen weight reference, so this is its only identity gate — stated here as the
   weaker of the two.
3. **The decomposition must have power somewhere.** At the deepest layer, where the residual path to
   the logits is shortest, the first-order prediction `size + align` must rank-correlate with the
   measured `|I_final|` at `ρ ≥ 0.70`. If it fails even there, the linear ontology is unfit at every
   depth, **world C wins, and the shallow layers are never read.**
4. **Sham-direction null.** Replace `Δu_ℓ` with a random unit vector of the same norm.
   `ρ̄(align_sham, log|I|)` must fall inside `±0.114` — two null `sd`s of the mean. If a random
   direction predicts the effect as well as the readout direction does, `align` is measuring vector
   length in disguise and no alignment claim is read.

## The two confounds, with their controls in the same run

**Depth mediates both terms.** The final LayerNorm makes `‖o‖` grow with residual-stream scale while
`Δu` is fixed, so `size` and `align` can each track depth and correlate with `log|I|` for a reason
that has nothing to do with heads. **Control:** every `ρ̄` is reported raw *and* partialled on
`(depth, μ_ℓ)` where `μ_ℓ` is the layer's mean `log|I|`. A share surviving only unpartialled is
reported as depth-mediated and carries no world.

**`|cos|` hides sign cancellation across heads.** The run also emits the signed inner product's
variance. If the signed and unsigned budgets disagree by more than `0.15` of the total, the result is
**UNVERIFIED and the disagreement is the finding.**

## Stopping rule and budget

- One-time checkpoint fetch, `≤ 9` GB, network time only, one retry per model on failure.
- `≤ 30` min GPU through `gpu-run`; `≤ 2` h CPU analysis.
- Control 1 mismatch → stop. Control 3 failure at the deepest layer → world C, close the per-head
  scalar ontology, do not read shallow layers.
- If the `3b` fetch or its identity gate fails while `1.5b` passes: **run `1.5b` alone, decide on its
  `2` strata, and mark cross-model generality out of scope. Never pool.**
- No new task, no third model, no second download.

## What each outcome kills

- **A** → "concentration" is head-output-norm dispersion. Every ablation scan in this repository
  becomes predictable from one clean forward pass, meaning a `40,000`-forward-pass measurement was a
  `120`-forward-pass measurement, and the *causal* reading of every published single-head effect
  dies with it.
- **B** → effect size is a geometric relation, not a magnitude. `R7`'s entire norm-matched apparatus
  is then controlling the wrong quantity, and the next object is the per-layer distribution of
  alignment angles — measurable over all heads × all layers pooled, which escapes the `n=12` bound
  that closed R24.
- **C** → the per-head scalar is not a head property. The object is propagation, `I_final` versus
  `I_all` becomes the primary axis rather than a robustness check, and their exact convergence at the
  last layer becomes the first data point of a propagation law instead of a curiosity.

In every branch the question is answered in nats² and the concentration/depth/width line stays shut.
