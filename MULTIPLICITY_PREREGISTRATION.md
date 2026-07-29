<!-- unbacked-ok: 36.76 27.39 27.41 -- the detector's own false-pass rates, before and after the
 D147 fix. A detector cannot emit the statistics of its own reference set into that set without
 circularity; same exemption and same reasoning as detectors/POWER_BREACH.md. Reproduced by
 `python3 detectors/prose_numbers.py --power`. -->
# Pre-registration — `A18` says there is no multiplicity correction. Correcting it would make this repository's headline STRONGER, and that is the problem.

Written 2026-07-29, **before the statistic was computed**, committed alone so git ordering rather
than my word establishes that the thresholds preceded the numbers.

## The charge, and it has been confirmed and left standing for a full session

`ADVERSARY.md:429` registered `A18` before the data. Two reviewers returned it `CONFIRMED`:

> **`31` decision rules yielding `12` headline verdicts, `alpha = 0.05` throughout, no correction
> anywhere.**

`D145` added two more. Nothing has been done, and the obvious repair — apply Bonferroni — is the
one thing that must **not** be done blind.

## Why the obvious repair is the wrong one here

Multiple testing inflates **false positives**. A correction lowers `alpha`, which makes it harder to
**reject** a null.

**But most of this repository's headline verdicts are absences.** *"The eight are not enriched"*
(`p = 0.8069`). `H-position` is registered as `p_pos >= ALPHA` — **failing to reject is a PASS
condition**. For every rule of that shape, lowering `alpha` makes the verdict **easier to satisfy**.

> **A blanket Bonferroni across these rules would strengthen this repository's central claims
> without a single new observation.** That is not rigour; it is a correction applied in the
> direction that flatters the author, and it is the same shape as this project's own named failure
> class — *a floor treated as measured when it was chosen*.

So the family must be **split by direction before it is corrected**, and the two halves reported
separately. I have not seen this done in the interpretability papers this repository cites, and I
have not been able to name the practice; it is registered here as a gap, not as a contribution.

## The instrument: breaking family size

The severity of any correction depends on `m`, the family size — and `m` is **bookkeeping, not
measurement**: `12` verdicts, `31` rules, `33` after `D145`. Publishing "significant after
Bonferroni at `m = 31`" would publish a number set by an arbitrary choice.

The family-size-free statistic:

```
m_break(rule) = floor( alpha / p )
```

**the largest family in which this verdict would still be rejected under Bonferroni.** It is a
property of the result, not of my bookkeeping, and it converts "corrected or not" into a scope.

**And it has a ceiling the data cannot raise.** A permutation test over `N` resamples cannot return
`p < 1/(N+1)`, so

```
m_break  <=  alpha * (N + 1)          regardless of the effect
```

`resolution_limit()` already found the per-head empirical null's minimum attainable `p` is
`1/169 = 0.005917`, so **no per-head result from that instrument can survive a family of `9`, no
matter how real it is.** The instrument ceiling is reported beside every `m_break`, so a large value
is never credited to evidence when it is owed to `N`.

## Design

The inventory is **derived, not hand-listed** — a hand-written population is how a check becomes
self-report, which this repository has already filed against itself. `headline.py --json` is walked
for `p`-shaped keys; each hit is then classified by **direction only**:

| direction | the rule's shape | what a correction does |
|---|---|---|
| **PRESENCE** | fires when `p <= alpha` | harder — correction is conservative |
| **ABSENCE** | fires when `p >= alpha`, or the claim is *"no effect"* | **easier — correction is anti-conservative** |
| **CONTROL** | a positive control, not a claim | neither; excluded from both families |
| **UNCLASSIFIED** | a `p`-shaped key I cannot assign | **counted and printed, never dropped** |

`UNCLASSIFIED` is reported as a count, because *the population a check iterates over is the check*.

## Registered thresholds

`alpha = 0.05`. `M_presence` = the number of PRESENCE rules the walk finds, **computed by the tool,
not chosen by me.**

| verdict | rule |
|---|---|
| **MULTIPLICITY-BITES** | `>= 1` currently-firing PRESENCE verdict has `m_break < M_presence` |
| **MULTIPLICITY-IMMATERIAL** | every firing PRESENCE verdict has `m_break >= M_presence` |
| **UNVERIFIED** | either positive control below fails |

And reported regardless of the verdict word, because it is the part I expect to matter:

1. **the count of PRESENCE verdicts that die below `m = 6`** — a family smaller than the number of
   metrics this repository reports per round;
2. **whether any ABSENCE verdict currently fails its `p >= alpha` requirement and would be
   MANUFACTURED by correction.** If one exists, that is a worse finding than anything in (1),
   because it means a correction presented as rigour would have created a claim.

## The strongest confound, written before the run

**`m_break` can be large for a bad reason.** A test with many resamples has a small floor, so a
result that merely hits the floor gets a big `m_break` while carrying no more evidence than
"nothing in `N` draws beat it". Six of this repository's `p` values are exactly `0.0005`, the floor
of a `2000`-draw null.

**Control, in the same iteration:** the instrument ceiling `alpha*(N+1)` is computed and printed
beside every `m_break`, and any rule whose `p` equals its own floor is flagged `AT_FLOOR` — its
`m_break` is a statement about `N`, not about the effect.

**Second confound: `m` is a choice.** Controlled by reporting `m_break` (family-size-free) as the
primary statistic, and by evaluating the verdict at **three** candidate family definitions —
`12` headline verdicts, `31` registered rules, and the tool's own `M_presence` — rather than one.

## Positive controls on the instrument itself

1. `p = 1e-9` must give `m_break = 50000000`; `p = 0.049` must give `m_break = 1`; `p = 0.06` must
   give `m_break = 0`. Asserted on synthetic input, not assumed.
2. The walk must find the `p` values already known to be in the emitter — in particular
   `mechanism.alignment.p = 0.045497725113744315`, whose own pre-registration already records that
   it fails Bonferroni at three tests. **If the walk misses it, the walk is not finding rules.**
3. `UNCLASSIFIED` must be printed even when zero, so a silent empty population cannot read as
   completeness.

## What each outcome costs me

**`MULTIPLICITY-BITES`** — which I expect — means one or more of this repository's *positive*
findings is significant only in a family of one, and every page carrying one must say so. The
candidates I can already name are `mechanism.alignment.p = 0.0455` (already flagged in its own
amendment) and `set_enrichment.L17H0_one_head_p = 0.0295858`.

**`MULTIPLICITY-IMMATERIAL`** would mean `A18` lands as a bookkeeping omission rather than a
substantive one, which is the outcome that costs me the *least* — and is therefore the one to
distrust.

**The finding I would least like:** that an absence verdict is currently failing and would be
manufactured by the very correction `A18` asks for. **That would make the requested repair a
fabrication engine**, and it is the reason the two directions are separated before anything is
computed.

## Boundary

This is about the repository's own decision rules, not about any model. `alpha = 0.05` throughout
because that is what was registered; nothing here argues it was the right choice. `m_break` assumes
Bonferroni; Holm and BH are less conservative, so a rule that survives Bonferroni at `m` survives
them, and one that dies under Bonferroni may still survive them — `m_break` is therefore a
**lower** bound on robustness, deliberately. The walk finds `p`-shaped keys in one emitter's output;
a registered rule whose `p` never reaches `--json` is invisible to it, and that miss is the
population limit of the whole exercise.

---

# Amendment 1 — the outcome, and the survivors survive on `N`

Appended 2026-07-29 after `detectors/multiplicity.py`. **No threshold above was changed.**

## Positive controls

| control | registered expectation | returned |
|---|---|---|
| `m_break(1e-9)` | `50000000` | asserted in `selftest()`, passes |
| `m_break(0.049)` | `1` | passes |
| `m_break(0.06)` | `0` — the instrument must have a failing branch | passes |
| the walk finds `mechanism.alignment.p` | present, else `REFUSED_WALK_MISSED_ANCHOR` | found, `0.045497725113744315` |
| `UNCLASSIFIED` printed even when zero | printed | `0` |

## The inventory, derived

```
p-values found by the walk   48
  PRESENCE   14      ABSENCE   21      RESOLUTION   10      CONTROL   3      UNCLASSIFIED   0
```

`RESOLUTION` was assigned **after** the first run, which put those ten in `UNCLASSIFIED` — recorded
as post hoc. It cannot move the verdict, which reads only the `PRESENCE` family, and
`resolution_limit()` already reports `0` BH discoveries for the rows concerned, so they were never
claims.

## Registered verdict: `MULTIPLICITY-BITES`

```
presence rule                              p        m_break   ceiling   at its null's floor?
condition_shape_rank p_lambda1 (x2)   0.0000499975      1000      1000    yes
ov_permutation_null  6 cells                0.0005       100       100    yes
selection_overlap    mean-of-ratios      0.0097998         5      2500    no
selection_overlap    L22H7 one head      0.0118343         4      2500    no
selection_overlap    sum-ratio           0.0149797         3      2500    no
set_enrichment       L17H0 one head      0.0295858         1      2500    no
mechanism            alignment partial   0.0454977         1         -    no
selection_overlap    median-of-ratios    0.2768545         0      2500    no  (does not fire)
```

`5` of the `13` firing presence verdicts have `m_break < M_presence = 14`, so the rule fires. The
same `5` also die below a family of `6`, which is smaller than the number of metrics this repository
reports per round.

## The part the registered rule did not ask for, and it is the finding

**All `8` surviving presence verdicts are pinned at their own null's resolution floor.
`n_surviving_with_graded_p = 0`.**

Their `p` is the smallest their instrument can return, so `m_break` measures **how many draws were
bought**, not how large the effect is: `20000` draws buy `m_break = 1000`, `2000` buy `100`, and two
results at the floor of the same null are indistinguishable however different their effects.

> **Not one presence verdict in this repository with a graded `p` survives its own family.** The
> ones that survive do so on `N`.

The confound registered before the run is exactly what produced this, and the control — printing
`alpha*(N+1)` beside every `m_break` — is what made it visible rather than flattering.

## The finding I was most afraid of, and did not get

```
absence verdicts a correction would MANUFACTURE   0
smallest absence p                                0.07035859282814344
```

Every absence `p` already exceeds `alpha` by a margin, so **no correction at any family size can
create or destroy one**. The repair `A18` asks for could not have fabricated a claim here. **The
repository's headline — a set of nulls — is multiplicity-immune. Its positive side-claims are not.**

## What this does not license

Deleting the five. `m_break` uses **Bonferroni**, the most conservative correction, so it is a
**lower** bound on robustness; Holm and BH are kinder and were not computed. And the
`selection_overlap` trio is a family of three by itself, inside which `mean-of-ratios` (`5`) and
`sum-ratio` (`3`) both survive. The honest statement is a scope, not a retraction:

> **these hold if the tests you count are the ones in their own round.**

## And the exercise broke the detector that checks it — `D147`

Quoting `0.0000499975` on the front page returned `unbacked` against a generator that emits exactly
that value. `detectors/prose_numbers.py`'s tokenizer could not read **scientific notation**, and
`json.dump` writes small floats that way. Measured on the live reference set:

```
distinct emitted values invisible to the detector          21
mantissa/exponent fragments injected into the BACKING set  26   ('05', '06', '09', ...)
```

**Both directions of the proxy ledger were broken by one missing alternation** — true numbers read
as unbacked, and a prose number could be backed by a bare exponent. `backs()` had the same bug a
second time: it computed precision as *digits after the dot*, which is `2` for `1.93e-08`, so it
rounded the generated value to two decimals — `0.0` — and rejected a correct quotation.

Fixed, selftest re-run, power re-measured (`36.76%`, unchanged on the `x.xx` row; `27.39` → `27.41`
on `xx.x`). **The tightened detector immediately flagged `13` prose numbers across three files that
had never been checked in the repository's life.** Four remain exempted with a written reason —
`hook_identity` loads a model, and the reference set is deliberately dependency-free.

## Boundary

About this repository's decision rules, not about any model. `alpha = 0.05` because that is what was
registered. `m_break` is Bonferroni-specific and is a lower bound on robustness. The walk sees only
`headline.py --json`; a registered rule whose `p` never reaches that output is invisible to it, and
that is the population limit of the whole exercise. Direction assignment is a hand-written table —
the one hand-written thing here — and a misassignment would move a rule between families silently.
