<!-- unbacked-ok: 0.9154 0.0569 0.0429
 -- THREE FIGURES BELONGING TO THE NAVIGATOR THAT SET THIS ROUND'S THRESHOLDS, not yet reproduced here.
 Its within-layer reliability of 0.9154 and its null standard deviations of the mean within-layer
 Spearman (0.0569 at n=12 over 28 layers, 0.0429 at n=16 over 36) come from its own simulations. My own
 measurement of the POOLED reliability, from the same R11 A/B item sets, is 0.9406 with an error sd of
 0.3989 nats -- emitted by R26_decomposition/attack_budget.py and backed. The three marked numbers are
 load-bearing on the thresholds below, so `kappa.py` reproduces them as its first act; whatever is still
 listed here after that run is still hearsay. -->
# R28 — κ, the log-gap between a head's measured effect and its own exact first-order prediction

Registered 2026-07-29, before any R28 code existed. Committed alone.

**Every threshold, world, control and stopping condition in this file was chosen by an independent
clean-context navigator and is transcribed, not paraphrased.** The author's own thresholds have now been
measured unfalsifiable or void four times in this repository — an `or` accepting either plant, a bar at
its own nominal coverage, a statistic computed on the curve holding its own confound, and most recently
an entire variance budget whose null is a point mass at the observed value.

## Why the previous statistic had to be replaced rather than repaired

R26's budget shares are **permutation-invariant**: `Var(size)/Var(log|I|)` never references which head
has which size. Measured over `10000` within-layer permutations, `max|Δ|` between `4.996e-16` and
`9.992e-16` with `P(null ≥ observed) = 1.0000` in all four cells. And the budget was never an identity:
`Var(log|I| − (size+align))/Var(log|I|)` came to `0.8418`, `1.6118`, `0.8358`, `1.6376` — above `1`
twice — so `residual_share` was one minus a ratio of the variances of two different variables.

The gap it was trying to describe is nonetheless real: the target's own item-sampling error is `0.3989`
nats, `0.0594` of `Var(log|I|)`, reliability `0.9406` over `336` cells from R11's disjoint item sets.
Roughly ten times smaller than what needs explaining.

## The measurement

One forward **and one backward** pass per item per model. A single backward pass yields
`g_{ℓ,h,i} = ∂margin_i/∂a_{ℓ,h,i}` for **every cell at once**, where `a_{ℓ,h}` is exactly the
`o_proj`-input slice that R10's hook zeroes — so the predictor is defined on the same tensor the
intervention acts on, not on a pullback that stops at the final norm.

```
P_{ℓ,h} = log | mean_i ⟨ a_{ℓ,h,i} , g_{ℓ,h,i} ⟩ |                    nats
κ_{ℓ,h} = log |I_{ℓ,h}| − P_{ℓ,h}                                     nats
Var(log|I|) = Var(P) + Var(κ) + 2·Cov(P, κ)                           nats²  ← identity BY CONSTRUCTION
C_{ℓ,h} = log( mean_i |⟨a,g⟩_i| ) − log | mean_i ⟨a,g⟩_i |   ≥ 0       nats
```

Both means are **signed** means over the same `120` items, so the predictor cancels across items exactly
as the target does — the fix, at the root, for R26 having taken `|cos|` inside the mean on the predictor
side while the target uses a signed mean. The identity holds because `κ` is *defined* as the difference,
which is the property R26's budget lacked. `C` is the cancellation index, free in the same pass, and the
first direct measurement of the confound R26 registered and never implemented.

**Deliverable: four numbers per cell, all in nats or nats², comparable across layer, head, support,
model and any future checkpoint. No verdict word.**

## Live worlds

- **A — TRUNCATED PULLBACK.** The write *is* the effect; R26 dotted it against a direction pulled back
  through the final RMSNorm only, discarding 27–35 layers of Jacobian. *Ontology: effect is a
  first-order property of the head's write, and the missing variance was a wrong readout direction.*
- **B — NONLINEAR REMOVAL.** The gradient is the right direction, but zeroing a whole head is far outside
  the linear regime, so no first-order account works at any depth. *Ontology: "head importance" is a
  property of the intervention's size, and every published single-head effect carries an `α` qualifier.*
- **C — ITEM CANCELLATION.** The scalar is `log|mean_i Δ_i|`; heads differ mostly in how much their
  per-item effects cancel, and the log of a near-cancelled mean is what makes the distribution wide.
  *Ontology: the width belongs to the item ensemble, not to heads — "different in different places" means
  "cancels differently in different places."*

## Prediction matrix — read as vectors

`[ R̄²(log|I| ~ P) within-layer , sd(κ) nats , ρ̄(κ, log‖a_h‖) , Var(C)/Var(log|I|) ]`

| | `R̄²` | `sd(κ)` | `ρ̄(κ, size)` | `Var(C)/Var(log\|I\|)` |
|---|---|---|---|---|
| **A TRUNCATED** | `≥ 0.70` | `≤ 0.45` | `\|·\| < 0.20` | `< 0.15` |
| **B NONLINEAR** | `0.20`–`0.50` | `≥ 0.80` | `≥ 0.50` | `< 0.15` |
| **C CANCELLATION** | `< 0.45` | `≥ 0.80` | `\|·\| < 0.20` | `≥ 0.30` |

Pairwise distinct in at least two coordinates (A/B in three, A/C in three, B/C in two). **No `or`
anywhere.** All-four-thresholds-miss is a fourth outcome and is reported as such, never folded into C.

## Why each threshold can fail in both directions and none sits at its own nominal coverage

1. **`R̄² ≥ 0.70` / `< 0.45`.** The floor is measured, not assumed: the one-predictor within-layer
   permutation null has mean exactly `1/(n−1)` — `0.0909` at `n=12`, `0.0667` at `n=16`, both confirmed in
   `R26_decomposition/attack_budget.py`. The ceiling is the target's own reliability. `0.70` sits far
   above today's best single predictor (`R²(size)` is `0.2863`, `0.1885`, `0.2740`, `0.1075`), so the bar
   is unmet now and reachable in principle.
2. **`sd(κ) ≤ 0.45` / `≥ 0.80` nats.** There is a hard arithmetic floor at `0.3989` nats — the measured sd
   of the target's own item-sampling noise. `0.45` is `13%` above that floor, so world A is demanding but
   not impossible; `0.80` is roughly half of `sd(log|I|) = 1.636`.
3. **`ρ̄(κ, size) ≥ 0.50` / `|·| < 0.20`, with a bound per model.** Null sd of the mean within-layer
   Spearman is `0.0569` at `(n=12, 28 layers)` and `0.0429` at `(n=16, 36 layers)`, so `0.20` is `3.5σ`
   and `4.7σ` and `0.50` is `8.8σ` and `11.7σ`. **Two bounds, one per model** — R26 used a single `0.114`
   for both, which was `32%` too wide for `3b`.
4. **`Var(C)/Var(log|I|) ≥ 0.30` / `< 0.15`.** `C ≥ 0` by the triangle inequality with a hard, attainable
   zero (a head whose per-item effects do not cancel), so the null is a point mass at `0` and this is not
   a residual category. `0.30` is where cancellation alone out-explains the entire first-order write as
   currently measured.
5. **Decided on `≥ 3` of `4` cells, never pooled.** The last layer is excluded from any both-supports
   count, because `I_all ≡ I_final` there at `max|Δ| = 0.000e+00`. The four cells share one predictor set
   per model, so the per-layer `I_final`/`I_all` rank correlation is reported — the dependence is a
   number, not an adjective.

## Controls, in order. No `κ` is read past either.

1. **The finite-difference limit.** For `8` cells (`2` layers × `4` heads) × `4` items, scale the head's
   write by `α ∈ {1, ½, ¼, ⅛, 1/16, 1/32}` and require `Δmargin(α)/α → ⟨a_h, g_h⟩` with relative error
   `≤ 1%` at `α = 1/32`, and monotone convergence. This is the definitional check that the gradient was
   taken on the tensor R10 zeroes; hooking the post-projection gradient instead would miss by exactly
   `W_O`. **Can fail. `192` forwards, seconds.**
2. **The two pullbacks must agree where they coincide.** At the deepest layer the remaining path is norm
   plus unembed, so `P` must rank-agree with R26's `size + align` at `ρ ≥ 0.90`. Two independently written
   pullbacks, one free cross-check. Disagreement means one of them is wrong — stop, and say which.

## The strongest confound, with its control in the same run

**`g` is evaluated at the unablated point while `a_h` is the vector removed, so `κ` contains the curvature
of the margin along `a_h`, which grows with `‖a_h‖` by construction.** A finding of "`κ` correlates with
size" is therefore partly guaranteed — and that correlation is world B's headline column. **Control, same
run:** an `α = ½` partial scan over `24` stratified cells (`4` per layer-sextile) × `120` items yields the
quadratic term `Δ(1) − 2Δ(½)` in nats. Regress `κ` on it and report `ρ̄(κ, size | curvature)`. If the size
correlation vanishes under that partial, world B's signature was curvature-by-construction and **B is not
carried** — reported as such, never smoothed over.

## What each outcome kills

- **A** → R26's budget dies outright, the propagation reading of the gap dies, and a `40320`-forward-pass
  instrument is replaced by `120` backward passes: a `336×` reduction, which is then the deliverable.
- **B** → the per-head scalar dies as a linearisable quantity, "importance" becomes explicitly
  scale-dependent, every single-head effect here and in the literature acquires an intervention-size
  qualifier, and the next axis is `α`, not depth.
- **C** → the scalar dies as a head property and the width relocates to the item ensemble. It also
  retro-explains R25's KV `η²`: KV-mates read the same keys, so their per-item sign patterns correlate and
  grouped cancellation would be the mechanism — a testable consequence and the next separator.
- **All four miss** → the first-order ontology is unfit *and* the width is not cancellation, which promotes
  `I_final` vs `I_all` from robustness check to primary axis.

## Stopping rule and budget

- Control 1 fails → **stop**, report which tensor the gradient was taken on, read no `κ`.
- Control 2 (`ρ < 0.90` at the deepest layer) → **stop**, the two pullbacks disagree, report both.
- `≤ 30` min GPU via `gpu-run`, `≤ 1` h CPU. Passes: `240` forward+backward, `192` control, `5760`
  curvature ≈ **`6200`**.
- `R̄² ≥ 0.70` with `sd(κ) ≤ 0.45` in `≥ 3` of `4` cells → world A, stop, that is the round.
- No new task, no third model, no new readout, no second download.
- `3b` has no A/B replicate, so its reliability ceiling is carried from `1.5b` and marked as such. If that
  carry decides a threshold, run `--seed-offset 400` on `3b` for the target only before deciding.
  **Never pool.**

## Held, on the same verdict

`R27_metric_gauge` is **held, not cancelled.** It costs `109440` forward passes to answer a *scope*
question rather than a *generative* one, and its headline statistic is defective today: `logsd` silently
drops cells with `|x| = 0`, and `flip` is exactly `0` for most cells, so "the width survives the readout"
would be compared across three different cell populations. Its `n_zero_cells` field is emitted and
consumed by nothing. If world C fires, the right gauge statistic is cancellation under each readout, not
`sd(log|·|)`. Run it after `κ`, with its own registration, and with `flip` replaced by a per-item quantity.
