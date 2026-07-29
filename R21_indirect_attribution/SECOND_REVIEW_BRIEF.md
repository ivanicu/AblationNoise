<!-- unbacked-ok: 0.0553 0.101 0.1603 0.187 0.1937 0.252 0.2629 0.2674 0.3687 0.3734 0.3819 0.3837 0.388 0.4355 0.449 0.5692 0.6503 0.6565 0.7139 0.7201 0.7311 0.8465 0.9447 3.427e-10
 THIS IS A THIRD-PARTY DOCUMENT REPRODUCED VERBATIM. The second-review
 pre-registration requires the briefer's text to be published unaltered so a reader can see what it
 chose to point at; editing its numbers to match this repository's emitters would defeat exactly
 that. Its figures are the briefer's own computations and are NOT this repository's claims -- the
 ones the attacker confirms are re-derived in tools/ and quoted from there, and the ones it does not
 confirm stay here as what a reviewer believed. -->
# The brief I did not write — published verbatim

Produced 2026-07-29 by an agent whose only instruction was *"decide where an adversary should look,
and say why"*, on the target directory. It attacked nothing. Registered in
[`SECOND_REVIEW_PREREGISTRATION.md`](SECOND_REVIEW_PREREGISTRATION.md), committed before dispatch.

**The forbidden-file control passed.** Its `FILES READ` line lists `38` paths and contains none of
`ADVERSARY_PREDICTIONS.md`, `defects.json`, `DEFECT_LEDGER.md`, `tools/adversary_recompute.py`, or
its output — and it never opened `README.md` at all, so it could not have seen the first review's
findings.

**Nothing below is a claim of this repository.** It is the input to the second review, kept so that
the overlap statistic can be read against what the briefer chose to name.

---

## 1. What the round claims

R21 takes the "indirect term" that R20 left unexplained — the part of a single attention head's `I_final` ablation effect that is not the head's own write — and splits it, by an exact algebraic identity on the final pre-norm residual, into five classes: `OWN` (the ablated head), `ATT` (the other 335 heads), `MLP` (28 blocks), `EMB` (residue), `NORM` (the RMSNorm gain change). Over 168 band heads (L14–L27, qwen2.5-1.5b, n=120 items, fixed clean comparator, final position), it registers a 0.50 dominance threshold and reports **`MIXED`** — `ATT 0.4845 / MLP 0.2341 / NORM 0.1706 / EMB ~0` — with three supporting readings: World NORM is declared dead (NORM carries only a sixth, so R20's `3.3x` is not a normalisation artefact); `ATT` wins only by membership (335 members at `0.000167` each vs MLP's 28 at `0.001698` — "10x more per member"); and `83–86%` of each class's motion cancels internally, so "the indirect term is a small net residue of a large amount of motion." It explicitly names no mechanism. Two amendments already retract: (1) the registered cross-run identity control against R10's frozen total, which failed at `1.9716` against a limit of `0.0122` and is repaired by a post-hoc 44-head comparator-stable subgroup; (2) the internal identity control, shown to be a tautology because `EMB` is defined as a residue.

## 2. ATTACK SURFACES, ranked

### A1 — The verdict `MIXED` is a choice of denominator, and the alternative denominator gives `ATTENTION-DOMINATED` on the registered population
**Rank 1. This flips the round's headline.**
`analyze.py:141` sets `denom = sum(abs(cell[c]) for c in ('att','mlp','emb','norm'))`. Because classes partly cancel against each other, absolute-normalising the denominator caps every share and mechanically biases the verdict toward `MIXED` — no class can exceed 0.50 unless it exceeds the sum of the absolute values of all others. The natural denominator for "share of the term being explained" is the **signed** sum of the non-`OWN` classes, i.e. the indirect term itself.

| denominator | ATT | MLP | NORM | verdict at 0.50 |
|---|---|---|---|---|
| `Σ|class|` (registered) | **0.4845** | 0.2341 | 0.1706 | MIXED |
| signed `Σ class` | **0.8465** | 0.0349 | 0.0553 | ATTENTION-DOMINATED |
| `|signed share|` | **0.9447** | 0.4355 | 0.3033 | ATTENTION-DOMINATED |

Median cross-class cancellation `|Σ signed| / Σ|.|` = **0.6132**.

### A2 — 38% of the registered population are heads whose effect is smaller than their own layer's head-to-head dispersion; excluding them also gives `ATTENTION-DOMINATED`
**Rank 2.** **64 of 168 band heads are below** their layer's `floor = sd/|base_margin|`. `Spearman(share_att, |total_r10|) = +0.3819`.

| population | n | ATT | MLP | NORM |
|---|---|---|---|---|
| below-floor | 64 | 0.3687 | 0.3837 | 0.2674 |
| ALL (registered) | 168 | 0.4845 | 0.2341 | 0.1706 |
| above-floor | 104 | **0.6503** | 0.1870 | 0.1338 |
| above 3× floor | 59 | **0.7139** | 0.1603 | 0.0792 |
| effect-size quartiles Q1→Q4 | 42 each | 0.3734 → 0.4131 → 0.5692 → **0.7201** | 0.388→0.152 | 0.252→0.101 |

### A3 — The registered decision rule says `UNVERIFIED`, and `analyze.py` silently drops the failed control out of the gate
`PREREGISTRATION.md:86` — `UNVERIFIED | either identity control below fails`. Control 1 failed at `1.971574` against `0.012176`, 162× over. `analyze.py:129` gates on `(ok_id_stable and ok_last and ok_own)` — **`ok_id` is not in the gate.**

### A4 — The one surviving control (`EMB`) is orthogonal to the round's entire output
It establishes only that no component's *write* escaped enumeration. It certifies nothing about the **ATT/MLP split**, the **per-head split inside ATT**, or the **NORM/component split** — and the split is the whole deliverable.

### A5 — The second "real control" is a near-tautology of the same class already retracted
`att == att_late` is algebra; for `L = 27`, `att == 0.0` exactly. Residual `median 3.427e-10, max 2.405e-08`.

### A6 — The "10× more per member" confound control divides by members that are structurally incapable of contributing
| | published | with effective membership |
|---|---|---|
| ATT per member | `0.000167` | `0.001255` |
| MLP per member | `0.001698` | `0.006231` |
| ratio | **10.17×** | **4.97×** |

### A7 — R20's `3.3251x` and `p = 2e-06` are superseded by R20's own analysis file, which R21 never cites
On R20's 122 usable heads, R21's shares move to `ATT 0.4490 / MLP 0.2629 / NORM 0.1937`.

### A8 — Control 3 correlates `OWN` against the wrong R20 variant
`Spearman(OWN, direct_renorm) = +0.9068` (margin `0.0068`); `Spearman(OWN, direct_linear) = +0.9999`; median relative discrepancy `0.3089`; sign disagreement `16 of 168`.

### A9 — The `85% cancellation` headline conflates across-component with across-item cancellation
Null `√(2/πn)` gives `0.090` (ATT, n=78) and `0.291` (MLP, n=7.5) against observed `0.1734` and `0.1392` — ATT is *more coherent* than random, MLP *more cancelling*. ATT's median is over 156 heads, MLP's over 168.

### A10 — The P7 plant's evidence is prose-only and self-exempted from the number checker
The planted arm's numbers have no checked-in artifact; `plant_missing_component.py`'s default `--out` is the published artifact's path; `_PRODUCER` names a path that does not exist.

### A11 — R21 dropped three refusal gates that R20 and R10 both carry
Including `REFUSED-READOUT-MISMATCH`. `base_margin` vs `r10_base_margin` agree to `2.4e-6` but are **printed, never asserted**.

### A12 — The 44-head repair explains less than a quarter of the failure it repairs
`Spearman(|err|, flip_rate) = +0.4831` (~23% of rank variance); `identity_vs_r10_max_stable = 0.0064726` on heads where the definitions should coincide; the limit is 19% of the median effect.

### A13 — "World NORM is dead" rests on A1's denominator and A2's population
NORM never approaches `0.50` under any tested combination — record CONFIRMED-under-all. But `3.8417x` uses `median|total_r10| / median|own|` while the same-convention figure is `4.1502`.

### A14 — Thin-ice items to sweep
`run.py:198` caps collection at `n_items*2`; `run.py:226` refuses only below 30 while every claim says `n=120`; `analyze.py:68`'s `1e-4` appears in no pre-registration.

## 3. Things judged NOT worth attacking
The additivity identity itself · the provenance chain · the vectorised projection · item-set equivalence with R10 · `EMB`'s magnitude as a completeness measure · numerical noise at class level · the NORM split convention (moves NORM ~2% of itself) · `_spearman` tie handling · whether `MIXED` should have been `MLP-DOMINATED`.

## 4. The single sentence to try hardest to break

> *"No class reaches `0.50`. `ATT` is the largest at `0.4845`."*

Across seven defensible populations and denominators the briefer measured `ATT` median share at **0.4490, 0.4845, 0.5294, 0.6503, 0.6565, 0.7139, 0.7311** — and at **0.8465** under the signed denominator. **The registered threshold, 0.50, sits inside that range.**
