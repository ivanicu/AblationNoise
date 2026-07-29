# Pre-registration — the two margins being divided are not the same quantity

Written 2026-07-28, **before the recomputed statistic existed** — the GPU job (`pueue 317`) was
submitted before this file, and the file is committed alone, so git ordering rather than my word
establishes that the thresholds preceded the number.

## The defect, found by an adversarial reviewer, and it is confirmed by reading the two files

`headline.margin_normalisation()` divides each task's floor by that task's baseline margin and
compares the two fractions. The reviewer's finding:

> *the two floors are genuinely the same statistic, but the two denominators are not the same
> quantity — R10's margin is conditioned on baseline correctness and R19's is not.*

Confirmed at the object, not from the description:

| | file:line | what it does |
|---|---|---|
| task A denominator | `R10_exhaustive/run.py:273-276` | `if argmax(rooms) != cor: continue` — **the item is dropped**, so `base_margin` is a mean over baseline-CORRECT items only |
| task B denominator | `R19_crossed_position_support/run.py:352` | `# NO CORRECTNESS FILTER, per R15's finding that filtering selects on position` — `baseline_margin_mean` is a mean over **all `1024`**, including the `25.88%` whose margin is **negative by construction** |

**R19's design choice is correct and it stays.** Filtering on baseline correctness selects on
position, and position is the factor this round crosses. What is wrong is using that number as a
*denominator against a differently-conditioned one*. Two estimands, one ratio.

## What is already known without running anything

An item is "baseline wrong" exactly when `margin = logit[correct] − max logit[other] < 0`, so
`m_wrong < 0` strictly. With `m_all = acc·m_corr + (1−acc)·m_wrong`:

```
m_corr  >  m_all / acc  =  1.6356854 / 0.7412109  =  2.206774
```

and therefore, since only the denominator moves,

```
residual_final  <  1.7416775 x 0.7412109  =  1.290950
residual_all    <  1.6197828 x 0.7412109  =  1.200601
margin_ratio    >  0.3653675 / 0.7412109  =  0.492933
```

**The published `1.7417` and `1.6198` are already known to be too large.** That much is arithmetic
and needs no GPU. What is *not* known is by how much, and the bound is one-sided — there is no
lower bound, so the finding can die entirely.

## The kill thresholds, registered before the measurement

The claim is *"dividing by the task's margin does not normalise the floor away"*, i.e. residual
`> 1`. The measurement kills it at:

| scope | dies if | equivalently |
|---|---|---|
| **final** | `m_corr >= 2.848836` | `m_wrong <= -1.838962` |
| **all** | `m_corr >= 2.649455` | `m_wrong <= -1.267904` |

Both are entirely reachable magnitudes on a readout whose correct-item margin is already known to
exceed `2.21`. **This is not a formality — the whole claim sits inside a window `0.44` wide in
`m_corr`, and the measurement decides which side of it the truth is on.**

| verdict | rule |
|---|---|
| **NORMALISATION-FAILS (survives)** | both recomputed residuals `> 1` |
| **PARTIAL** | exactly one recomputed residual `> 1` — and the *"same direction in both scopes"* internal replication, which is this comparison's only claim to being more than `n=1`, is **dead** |
| **NORMALISATION-HOLDS (killed)** | both `<= 1` — the floor IS a fixed fraction of the task's dynamic range once the denominators are matched, and the front page's `1.7417` was an artifact of a definitional mismatch |

## The strongest confound, written before the run

**Re-running the baseline pass could silently change the dataset.** If the recomputed
`margin_all_items` differs from the frozen `1.6356853898614645`, then the items, the seed, the
tokenizer or the encoder moved, and the correct-only figure computed alongside it describes a
*different* experiment — in which case nothing here is comparable and the run is void.

**Control, in the same iteration:** `--baseline-only` re-runs the identical code path (the diff
adding it is `+41 / -0`, verified with `git diff --stat`, so no existing line changed) and emits
`margin_all_items` beside `margin_baseline_correct_only`. **The all-items figure must reproduce
`1.6356853898614645` exactly, and the accuracy must reproduce `0.7412109375`.** If either misses,
the verdict is `UNVERIFIED` and no residual is quoted.

Second: `_CODE_VERSION` is `sha256(run.py)` and it necessarily moved when the flag was added, so
the emitted file will not carry the frozen run's hash. That is a fact about the file, not about the
computation, and the `+41 / -0` diff is the evidence that the baseline path is unchanged.

Third: `max_margin_wrong` is emitted. It must be `< 0`. If any "wrong" item has a non-negative
margin, the correctness predicate and the margin disagree and the whole decomposition above is
unsound.

## What each outcome costs me

**If it survives:** the front page keeps the claim but **must quote the matched numbers**, and must
state that the previously published `1.7417 / 1.6198` were computed against a denominator
conditioned differently from the one they were compared to. The magnitude shrinks by at least
`26%` regardless of outcome.

**If it dies:** *"the floor is not a fixed fraction of the task's dynamic range"* — a sentence that
supports this repository's central headline — was an artifact of my own definitional mismatch, on
the only cross-task comparison the repository has. **That is the unwelcome branch and it is why
this is worth running.** It would also be the twelfth instance of this repository's own named
failure class: a number reported without the scope over which it holds.

## Boundary

`n = 2` tasks. This is a post-hoc observation, not a registered test, and this amendment does not
convert it into one — it repairs an arithmetic mismatch inside it. One model, `qwen2.5-1.5b`, one
metric (`signed_margin_drop`), floors defined as `2 sd` over the `L14`–`L27` band. Matching the
denominators does not make the two tasks differ in one factor: they still differ in line count,
prompt structure and item count simultaneously, which is why this stays out of the transport table.
