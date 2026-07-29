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
