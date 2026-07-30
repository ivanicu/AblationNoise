<!-- unbacked-ok: 3.1 10.95 0.061 0.0456 0.0025 0.937
 -- SIX FIGURES ASSERTED BY THIS FILE AND NOT YET MEASURED HERE. The Gaussian-120 null for max/rms (3.1),
 the single-item-dominated limit (10.95 = sqrt(120)), the split-half correlation's null sd (0.061), the
 per-cell and layer-mean binomial sds for the sign fraction (0.0456, 0.0025), and the within-layer
 reliability ceiling (0.937) are all thresholds' justifications rather than results. The run emits every
 one of them -- the two combinatorial nulls by simulation in the same process -- and whatever is still
 listed here afterwards is still an assertion. The numbers this file uses as EVIDENCE, by contrast, are all
 backed by R29_cancellation/decompose_on_disk.py. -->
# R29 — the per-item effect vector R10 computed 218,880 times and discarded

> ## ⛔ RETRACTED 2026-07-30 — BOTH COORDINATES ARE IDENTITIES ON TWO PUBLISHED COLUMNS
>
> The body below is preserved unedited, because a registration that is rewritten after its result is
> not a registration. What it registered does not stand.
>
> ```
> rms² = mean² + (n−1)/n · sd_i²      sd_i = sem·√n
> ⇒  G = 0.5·log(mean² + (n−1)·sem²)        Λ = 0.5·log(1 + (n−1)/snr²)
> ```
>
> `(mean, sem) ⟺ (G, Λ)` is a **bijection**, so the split is a change of coordinates on `per_head` and
> `per_head_sem` — both already published in `R11_instrument_noise/results/`. Verified at `max|dev|
> 1.332e-15` for `Λ` over 336 cells, and reproducible from those two columns with **zero forwards** at
> `corr 0.99999962`. **The 2,976 forward passes bought nothing for either coordinate.**
>
> **So `G`'s `0.9982` replication, quoted below and reported at the time as this round's strongest
> result, is a property of R11's two columns and not of anything this scan measured.** A restatement
> inherits its source's reliability and adds no information.
>
> Also retracted, on separate grounds, all in `retract_w1.py` with every figure regenerated there:
> the `W1` reading (an SNR-preserving null reproduces it — sign-fraction null median `0.7333` against a
> `W1` bar of `0.65`); the claim that `W3` was positively excluded (its bar needed a *median*
> `max|Δ|/rms ≥ 6.5` while the *max* over every cell is `4.4596` and `5.4534` — unreachable, dead on
> arrival like `W0`); and the jackknife as the instrument floor (`0.0933` nats against a direct
> off0-vs-off400 replicate of `0.3910`, `4.19×` optimistic).
>
> **What survives the round:** the persisted per-item tensors, which are the only object here that is
> not a function of the two published columns.


Registered 2026-07-29, before any R29 measurement code existed. Committed alone.

**The worlds, the prediction matrix, every threshold, both controls and the stopping rule are an
independent clean-context navigator's and are transcribed, not paraphrased.** Five of the author's own
thresholds have been measured unfalsifiable, void, or below the instrument's precision floor in this
repository, and the most recent — an entire variance budget whose null was a point mass — was written in
the round created to escape exactly that defect.

## Why this and not more of κ

R28 is closed. No `κ` was read in four runs, and the reason is not the control: its decision apparatus
could not answer its question even had control 1 passed. `Var(C)/Var(log|I|)` is permutation-invariant —
the R26 defect reappearing inside the round written to escape it — `sd(κ)` is pinned to the B/C side by
between-layer structure alone, world A was arithmetically excluded by its own variance budget against the
measured error, and `ρ̄`, the sole remaining separator, had its registered curvature control computed and
never consumed.

What replaces it is already half-visible. The published scalar is `log|mean_i Δ_i|`, and splitting it
pointwise into `G = log rms_i(Δ)` and `Λ = G − log|mean_i Δ| ≥ 0` gives, across R11's two disjoint item
sets over the same `336` cells:

```
coordinate   corr(A,B)   sd(A−B) nats
log|I|         0.9406       0.5650
G              0.9982       0.0682
Λ              0.8722       0.5526
```

`(G, Λ)` from a disjoint item set predicts `log|I|` at within-layer `R̄² = 0.9217`, above the target's own
replicate ceiling of `0.9019`. What a summary cannot say is **what shape produces `Λ`**, and **whether it
belongs to the head or to the item ensemble** — which is `为什么不同地方会有不一样呢` exactly.

## The measurement

Re-run R10's and R18's ablation and **keep the `120`-vector `Δ_{c,i}` instead of collapsing it to its
mean.** Per cell emit `G_c` and `Λ_c` in nats; per layer emit the eigen-structure of the `120 × NH` matrix
of unit-normalised item patterns. Both models, both supports, and both item sets (`--seed-offset 0` and
`400`) for `1.5b`.

**Deliverable: two per-cell quantities in nats, comparable across layer, head, support, model and any
future checkpoint.** Not a tool, not a checker, not an audit.

## Live worlds

**W0 — ONE ITEM DIRECTION, MANY GAINS** is **killed on arrival and not carried.** If `Δ_{c,·} ≈ g_c u_ℓ`,
then `Λ_c` is *exactly constant* within a layer. Observed within-layer `sd(Λ)` is `0.9164` nats against a
per-cell `Λ` precision of `0.5526/√2 = 0.391` nats. Refuted from data already on disk, before the run.

- **W1 — COHERENCE IS A HEAD PROPERTY.** Item patterns are far from collinear, `Λ` varies between heads at
  fixed gain, and it reproduces across item splits. *Ontology: the published scalar collapses two nearly
  independent quantities; head importance is a pair `(G, Λ)` in nats and the width is two-dimensional.*
- **W2 — DEGENERATE RATIO.** `Λ` is large exactly where `|mean|` sits at its own item-sampling floor; the
  per-item distribution is symmetric about ≈`0` and `Λ` carries no head information beyond `1/SNR`.
  *Ontology: the excess width is not a property of anything. `|mean_i Δ|` is the wrong statistic, `rms_i Δ`
  is the right one, and the low-SNR cells must be reported as intervals.*
- **W3 — A FEW ITEMS.** `Λ` is driven by heavy tails: a small number of items supply the effect and the
  rest cancel. *Ontology: the object is an item × head interaction table, "which items" replaces "how
  much", and every pooled floor in this repository is a floor over the wrong index.*

## Prediction matrix — read as vectors

`[ sd_w(Λ | log rms) nats , λ₁/Σλ , split-half r(Λ₁,Λ₂ | log rms) , med_c max_i|Δ|/rms , med_c sign frac ]`

| | `sd_w(Λ\|rms)` | `λ₁/Σλ` | split-half `r` | `max/rms` | sign frac |
|---|---|---|---|---|---|
| **W1 head property** | `≥ 0.40` | `≤ 0.60` | `≥ 0.60` | `≤ 4.5` | `≥ 0.65` |
| **W2 degenerate ratio** | `≥ 0.40` | `≤ 0.60` | `≤ 0.25` | `≤ 4.5` | `≤ 0.55` |
| **W3 few items** | `≥ 0.40` | `≤ 0.60` | `≥ 0.60` | `≥ 6.5` | `≤ 0.55` |

W1/W2 differ in two coordinates, W1/W3 in two, W2/W3 in two. **No `or` anywhere.** All-miss is a fourth
outcome, reported as such and never folded into W2.

## Thresholds, and why none is at its own nominal coverage or below the instrument's floor

1. **`sd_w(Λ | log rms) ≤ 0.15` / `≥ 0.40` nats.** The instrument's floor is the **jackknife-over-items sd
   of `Λ`, emitted per cell.** **Gate: if the median emitted precision exceeds `0.15` nats, the low side is
   below the floor and this coordinate returns UNVERIFIED rather than passing** — the defect that cost R28
   three runs, pre-empted. The high side is not free either: the raw within-layer `sd(Λ)` is contaminated
   by SNR, and residualising on `log rms` is precisely what removes that.
2. **`λ₁/Σλ ≥ 0.85` / `≤ 0.60`.** Two nulls **simulated in the same process and emitted**: iid-Gaussian
   unit-norm columns, and a **random-resign** null on the observed columns, which destroys shared structure
   while preserving every magnitude. `0.60` sits between the iid null and the collinear limit of `1.0`, at
   neither.
3. **Split-half `r(Λ₁, Λ₂ | log rms) ≥ 0.60` / `≤ 0.25`.** Null is `0` with sd about `0.061`, so `0.25` is
   `4.1σ` and `0.60` is `9.8σ`. **Gated on the RAW value, with Spearman–Brown reported beside it** — the
   correction is a ceiling statement and may never be the thing that passes. Attenuation at `60` items per
   half is a real failure route for W1, which is why its bar is `0.60` and not `0.90`.
4. **`med max|Δ_i|/rms ≥ 6.5` / `≤ 4.5`.** Gaussian-`120` null is about `3.1`, simulated and emitted; the
   single-item-dominated limit is `√120 = 10.95`. `4.5` is above the null and `6.5` well below the limit.
5. **`frac(sign Δ_i = sign mean) ≤ 0.55` / `≥ 0.65`.** Hard attainable null of exactly `0.5`, binomial sd
   `0.0456` per cell and `0.0025` on the layer mean. **The per-cell distribution is reported, not only its
   mean** — a layer mean at `n=336` sits `20σ` from the null and would look decisive on nothing.
6. **Decided on `≥ 3` of `4` cells, never pooled.** The last layer is excluded from any both-supports count
   because `I_all ≡ I_final` there at `max|Δ| = 0.000e+00`, and the per-layer `I_final`/`I_all` rank
   correlation is emitted so the dependence is a number rather than an adjective — both registered in R28
   and both left unimplemented there.

## Positive control, and no `Λ` is read past it

The per-item pipeline must **reproduce R10's and R18's published `per_head` means, and R11's `per_head_sem`
where present, cell by cell on the same seeds**: `max|Δmean| ≤ 1e-5` margin-nats over all `336`/`576`
cells, `max|Δsem|/sem ≤ 1e-3`, and `mean_i(base)` matching the published `4.476821851730347` and
`6.637211505572001` to `1e-5`.

**It can fail.** Batching changes the reduction order, a padded batch puts the query at the wrong position,
and the `[:, -1]` slice is exactly what a dead guard in R28 was worried about. It is a positive control in
the required sense — the instrument returns a **known non-zero published value** before any null or any
zero is admissible. **Fail → stop, report the max per-cell discrepancy, read no `Λ`.**

This also discharges something R28 left on the table: it set a head's write to zero, recorded the result,
and never compared it to R10's `per_head` for the same cell — the repository's strongest positive control,
available for free and untaken.

## The two confounds, with their controls in the same run

**`Λ` is a deterministic function of `(mean, sd)` with `mean` in its denominator**, so "`Λ` explains the
width of `log|I|`" is definitional, and any same-item-set statistic inherits it. **Control:** every `Λ`
statement is reported in **split-half form** — `Λ` from items `1`–`60` against `log|I|` from items
`61`–`120` — **beside** the same-set form, in one table, and the gap **is** the confound's size in nats.

**`λ₁/Σλ` is inflated by a shared item-difficulty direction** with nothing to do with attention.
**Control, same run:** report `λ₁/Σλ` raw *and* after projecting out the layer-mean `Δ` vector, plus the
random-resign null with identical marginals.

## What each outcome kills

- **W1** → the per-head scalar dies as a scalar. Every single-head effect here and in the literature
  becomes `(G, Λ)` in nats, and "the floor" becomes two floors. R26, R27 and R28 are subsumed: they each
  asked which single quantity generates the width, and the answer is that none does.
- **W2** → `|mean_i Δ|` dies as the target. The headline count is recomputed on `rms_i Δ`, the low-SNR
  cells become intervals, and R28's world C and R27's gauge question are both moot — the cancellation they
  wanted to attribute to heads is the target's own resolution limit.
- **W3** → the object is an item × head table, "which items" replaces "how much", and every pooled floor
  in this repository is a floor over the wrong index.
- **All miss** → the per-item vector does not carry the structure either, and the next axis is the
  intervention size `α`, not the item ensemble.

## Stopping rule and budget

- `2976` batch-`120` forwards against the `218,880` single forwards this replaces — about `74×` fewer model
  evaluations for `120×` more data per cell. `≤ 40` min GPU via `gpu-run`, `≤ 30` min CPU.
- **Implementation trap that is part of the plan: `120 × 121 × 151936` float32 logits is `8.8` GB. Chunk at
  `40` and slice `[:, -1]` inside the loop.** Prompts are equal length, established by a batch tokenising
  without padding, so no padding is needed and none may be added.
- Positive control fails → stop.
- **Any coordinate whose emitted precision exceeds its own threshold gap → UNVERIFIED on that coordinate,
  never folded into a world.**
- No new task, no third model, no new readout, no new download.
