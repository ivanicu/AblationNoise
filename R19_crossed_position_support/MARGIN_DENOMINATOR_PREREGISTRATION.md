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
| task B denominator | `R19_crossed_position_support/run.py:352` | `# NO CORRECTNESS FILTER, per R15's finding that filtering selects on position` — `baseline_margin_mean` is a mean over **all `1024`**, including the `265` whose margin is **negative by construction** |

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
exceed the bound `2.206774`. **This is not a formality — the whole claim sits inside a window `0.44` wide in
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

---

# Amendment 1 — registering the SECOND half of the repair, before it is computed

Appended 2026-07-28. The denominator has been recomputed (`pueue 318`/`319`, both landed) and its
verdict is fixed by the rules above; it is written up in Amendment 2. **This amendment registers a
test that has not been run**, and is committed alone, before the tool that runs it exists.

## Matching the denominator is only half the repair, and I did not notice until after

R10's denominator is baseline-correct-only. So is **R10's numerator**: every per-head drop it
averages comes from an item that survived `run.py:273`. R19's numerator averages all `1024`. So
`floor_A / margin_A` and `floor_B / margin_B` differ in **both** terms, and Amendment 2 fixes one.

**The direction is not obvious and must not be guessed.** Items with a wrong baseline have negative
margins and are plausibly noisier under ablation, which would inflate `floor_B` and inflate the
residual — but they could equally be *saturated* and move less, which would deflate it.

## The test

The frozen `r19_crossed_qwen2.5-1.5b.json` stores each head's mean effect at `(base, pos)`
granularity, each cell the mean of `N_NUISANCE = 2` replicates. `pueue 320` emitted
`n_correct_by_base_pos`, so each cell is known to be `2/2`, `1/2` or `0/2` baseline-correct:
**`315` / `129` / `68` of `512`**, reconciling to the `759` correct items exactly.

Restrict to the `315` fully-correct cells, recompute each head's mean, recompute the floor as the
same `2 sd` over the same `168` band heads, and recompute the residual with **both** terms matched.

## The strongest confound, written before the run, and it is the whole reason for the control

**Dropping `197` of `512` cells changes the floor by itself.** Fewer cells per head means a noisier
per-head mean, and `2 sd` across heads of a noisier quantity is **larger** — so a rise in the
restricted floor is the DEFAULT expectation under no effect whatsoever, and reading one as evidence
about baseline correctness would be reading sampling noise as a finding.

**Control, in the same iteration:** a matched-count random restriction. Draw `315` of the `512`
cells uniformly at random, recompute the floor, repeat `N_DROP = 2000` times, and report the
observed restricted floor as a **percentile of that distribution**. The correctness restriction is
informative only where it leaves that distribution.

**Second confound, and it is this round's own subject:** baseline correctness is not independent of
position — that is exactly why `run.py:356` refuses to filter, citing R15. The retained cells will
have a different position composition from the full grid, so any change may be a position effect
wearing a correctness label. **The position composition of the retained cells is reported beside
the floor**, and the random control is drawn without regard to position, so it does *not* absorb
this — it is stated as a limit, not controlled away.

## Registered thresholds

| verdict | rule |
|---|---|
| **NUMERATOR-MATTERS** | observed restricted floor outside the central `95%` of the random-drop distribution, in either scope |
| **NUMERATOR-IS-CELL-COUNT** | inside it in both scopes — the change is the restriction's cost, not baseline correctness |

And the number reported regardless of the verdict word: **the fully-matched residual in both
scopes, against Amendment 2's denominator-matched `1.0466` / `0.9734` and the published
`1.7417` / `1.6198`.**

## What each outcome costs me

If the fully-matched residual falls below `1` in **both** scopes, the claim *"dividing by the task's
margin does not normalise the floor away"* is dead on the only cross-task comparison this
repository has, and the front page's `1.7417` was an artifact of comparing two ratios that shared
neither a numerator definition nor a denominator definition.

## Boundary

`n = 2` tasks. The restriction is at `(base, pos)` cell granularity, not item granularity, because
that is the resolution the frozen result stores — the `129` half-correct cells are dropped rather
than partially credited, which is a coarser filter than R10's per-item one and is not equivalent
to it.

---

# Amendment 2 — both outcomes, and the half-fix was worse than the original error

Appended 2026-07-28 after `pueue 318`/`319`/`320` and `tools/matched_denominator.py`. **No threshold
above was changed.**

## Positive controls

| control | registered expectation | returned | |
|---|---|---|---|
| `margin_all_items` reproduces the frozen `1.6356853898614645` **exactly** | exact | `1.6356851365417242`, off by `-2.5e-07` | **FAILS AS WRITTEN** |
| `baseline_accuracy` reproduces `0.7412109375` | exact | exact | pass |
| `max_margin_wrong < 0` | `< 0` | `-0.00582122802734375` | pass |
| reconstructing the per-head mean from the `(base, pos)` grid matches the published `base` array | `< 1e-6` | `1.93e-08` (final), `1.58e-08` (all) | pass |
| observed floor vs matched-count random drop | registered as the verdict rule | percentile `1.0000` both scopes | fires |

**The exactness control fails and is reported as failed.** Two identical reruns (`318`, `319`)
agree with each other **bit for bit** on every emitted value, and both miss the frozen figure by the
same `-2.5e-07`. So it is *not* run-to-run non-determinism now; something differed between the
frozen scan and this box today, and **what** is `UNVERIFIED` — I did not establish it, and a
plausible story about cuBLAS kernel selection is not a measurement. The magnitude is `1.5e-07`
relative, six orders below the floor it feeds, so it cannot move a residual quoted to four decimals.
**It is recorded rather than rounded away because "the frozen number is not bit-reproducible by its
own command on its own box" is exactly the kind of fact this repository exists to report.**

**And the reconstruction control caught its own harness first.** Its first run rejected a grid that is in
fact consistent to `1.93e-08`; the cause was in the check, which averaged the whole `(64, 3)` metric
array instead of column `0`. A control that had been written to pass
would have said nothing; this one failed loudly against correct data, which is the only reason its
later `1.93e-08` is worth anything.

## Part 1 — the denominator

```
margin over all 1024 items          +1.6356851        (n = 1024)
margin over baseline-correct only   +2.7219879        (n =  759)
margin over baseline-wrong only     -1.4756500        (n =  265)
```

`m_corr = 2.721988` sits **between** the two registered kill thresholds — above `2.649455`, below
`2.848836`. The registered rule therefore returns **`PARTIAL`**:

```
                          final     all
published               1.7417    1.6198
denominator-matched     1.0466    0.9734     <- `all` is below 1
```

and with it, *"it misses in the same direction in both scopes"* — the only internal replication
`n = 2` can offer — **is dead under this repair.**

## Part 2 — the numerator, registered in Amendment 1

Restricting to the `315` of `512` cells whose both replicates are baseline-correct:

```
                       floor_final          floor_all
full grid                0.309927            0.577951
random drop of 315       0.311024            0.578332     [0.298520,0.323968]  [0.553164,0.604515]
correctness-restricted   0.417063            0.806338     percentile 1.0000 in both scopes
```

Registered verdict: **`NUMERATOR-MATTERS`**. Dropping cells at random costs essentially nothing
(`0.309927` -> `0.311024`); dropping them *by baseline correctness* widens the reference
distribution by `35%` (final) and `40%` (all). **The width of the floor depends on which items you
condition on, inside one task, one model and one metric.**

**Post hoc, unregistered, and it weakens the above:** the kept cells are position-skewed
(`[64, 61, 42, 28, 23, 24, 29, 44]` of `64`) — R15's finding restated. A null holding those
per-position counts fixed reaches `0.340379 [0.328496, 0.352252]` and
`0.655241 [0.634458, 0.675443]`, still far below the observed. So position composition accounts for
part of the rise and not most of it. This control was added after seeing the result and can only
subtract from the claim, which is the only direction an unregistered control may move it.

## The three residuals, and the sentence they force

```
                                 residual final    residual all    same direction
published    (neither matched)       1.7417           1.6198            yes
denominator only                     1.0466           0.9734            NO
BOTH terms matched                   1.4084           1.3580            yes
```

> **The half-fix is farther from the truth than the original error.** Matching only the
> denominator — the repair the reviewer's finding literally asks for, and the one I set out to make
> — puts the `all` scope at `0.9734` and would have retracted a claim the matched comparison
> supports at `1.3580`. **A two-term mismatch corrected in one term is not a partial improvement.**

That is a new entry for this repository's overshoot list, and it is not one of the eleven already
on it: *a correction applied to one of two coupled definitions can overshoot the truth in a
direction the original error did not.*

## What survives, at its correct size

The claim *"a floor cannot be made portable by dividing by the task's margin"* **survives**, at
`1.36`–`1.41×` rather than `1.62`–`1.74×`. About `20%` of the published excess was an artefact of my
own definitional mismatch. The registered forward prediction on a third task is unchanged in
direction and its target moves: on a task harder than R19's, `floor / margin` in the `final` scope
should exceed R19's **matched** value, not its published one.

## Boundary

`n = 2` tasks, one model, one metric, `2 sd` floors over `L14`–`L27`. The restriction is at
`(base, pos)` granularity, so the `129` half-correct cells are dropped rather than partially
credited — a coarser filter than R10's per-item one, and not equivalent to it. The correctness
selection is confounded with position composition by construction, quantified above and not removed.
Nothing here revises any R19 verdict: the round's four hypotheses stand on the unfiltered numbers,
which remain the right ones for the question that round asks.
