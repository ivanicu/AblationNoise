<!-- unbacked-ok: 17.2 24.3 41 500 700 35 -- the detector's own false-pass rate, which cannot
 enter the reference set without infinite recursion (measuring it requires building the set).
 17.2% was measured 2026-07-28 at ~500 reference values, 24.3% the same day at >700. The LIVE
 figure is printed by every `make verify` run, so these two are dated history, not the current
 value -- read the gate, not this page. -->

# What an adversary will overturn — written before one runs

2026-07-28. **No independent challenger has reviewed this repository.** Every claim in it is
`[unchallenged]`, which is not the same word as *clean*, and the difference is the point: a reviewer
sampled from the same weights that wrote the material can only attack what its author already
anticipated — which is exactly why those parts read as fluent.

So this file does the only honest thing available: **it predicts, in advance and in rank order, what
a hostile clean-context reader will find.** When one eventually runs, its findings score this list,
and *that* number — how well the author predicted his own blind spots — is worth more than any
individual verdict.

**How to score it.** For each row: did the adversary raise it? Did it land at the predicted
severity? A row raised and landing *harder* than predicted is a miss. A row not raised at all is
also a miss — it means effort was spent defending something nobody attacks.

---

## The predictions

### A1 · "Eight published effects" oversells the population — `LANDS, and I expect it to land hard`

> The set is E132b's eight heads: **five were read-head *candidates*, one (`L22H7`) an independently
> proven copy head**, two unlabelled. The front page calls them "eight published single-head
> effects" and R1's own README calls the candidate framing a strength.

> **⚠ THE SENTENCE ABOVE IS WRONG, AND IT WAS STILL WRONG HERE FOUR ROUNDS AFTER BEING CORRECTED
> ELSEWHERE.** [R16](R16_selection_vs_effect/) read the source experiment instead of my note about
> it: `E132b`'s `sel` dict has **seven** keys, plus `L22H7` which `E132` ranked **first** on room
> attention. So the composition is **seven selected candidates plus one externally-known copy head**,
> not *five / one / two*. That correction was filed as `D80` — **and it landed on the prior-effects
> note only.** The identical wrong sentence sat here, in the file whose entire job is to score me
> when I am wrong. Kept above rather than edited, because a prediction file that silently repairs
> itself always scores well.

**The attack:** a candidate is a hypothesis, not a result. Finding that five hypotheses fail to clear
a noise floor is close to tautological — R1's own set-level data says the READ set sits at the
`46.7`th percentile of the null, i.e. *there was nothing there to find*. **The number of
independently established mechanisms shown to be inside the floor is `1`, not `8`.**

**My assessment: this is correct and the framing should change.** The one that matters is `L22H7`,
and it carries the whole claim by itself. I predict the adversary states it more sharply than this
paragraph does.

> **ACTED ON, same day, before any adversary ran.** The front page no longer says "eight published
> effects"; it leads with the one established mechanism. **This row can no longer be scored** — a
> self-corrected prediction is not a tested one, and the only evidence it was written first is the
> commit order. Recorded here rather than deleted, because a prediction file that quietly drops the
> rows its author fixed is a file that always scores well.

### A2 · The whole repository is one synthetic task — `LANDS`

One 4-way binding task, one prompt template, `n=120` items, one readout (margin), four models of
which one supplies every headline number. Individual pages state the scope; **the headline sentence
does not.**

**Prediction:** the adversary will say the title claims something about ablation and the evidence is
about *this task*. I agree, and I do not currently have a second task.

### A3 · `k=1` is the wrong granularity, and the repository's own data says so — `LANDS, and this is the one I would rank first if I were attacking`

The front page already concedes the `k=1` regime is **sub-behavioural**: the floor is `9.9%` of the
distance to a different answer, the largest effect `10.4%`. And R1's set-level result shows the
**COPY circuit at the `0.0`th percentile of the k=5 null** — a real, enormous, localised effect.

**The attack:** if ablating the actual circuit produces an unmistakable effect and ablating one of
its heads does not, the finding is *"single heads are the wrong unit"*, not *"published effects are
noise"*. The repository has the data for the stronger, more useful claim and leads with the weaker,
more provocative one.

**My assessment: I think this substantially lands**, and the counter — that single-head effects
*are* what gets published, so measuring their floor is the point — is a reason the work matters, not
a reason the framing is right.

> **ACTED ON, same day.** The front page now leads with *"the single head is the wrong unit"* and
> puts the `k=5` circuit result (`0.0`th percentile, `−1.4279` against a `4.477` margin) beside the
> single-head number instead of three screens below it. **Also unscoreable now**, for the same
> reason as A1.

### A4 · `2 × sd` is a normal-distribution threshold on a visibly non-normal null — `PARTLY LANDS`

`L22`'s twelve heads: `+0.3977, −0.3379, −0.2214, +0.2049, −0.1317, +0.0751, −0.0688, −0.0260,
−0.0256, −0.0199, +0.0194, +0.0099`. Heavy-tailed, asymmetric, `n=12`.

**Prediction:** the adversary proposes an empirical percentile instead. **I do not know whether the
count changes** — that check is not in the repository and should be. Predicted severity: medium,
because R1 *already* reports percentiles at the set level and the two conventions coexist unreconciled.

> **RESOLVED 2026-07-28 — the first row in this file to be settled, and it scores me BADLY.**
> The count does **not** change: leave-one-out, each head judged by a null excluding it, still `9`.
> The *interpretation* breaks instead. Excess kurtosis is `+7.43`, and beyond `2 × sd` a normal
> gives `7.6` of `168` while a Laplace gives `9.9` — observed `9`. **So "nine heads clear the floor"
> is the tail a heavy-tailed distribution hands you for free**, and the front-page inference it
> carried (*"so single-head ablation resolves effects here perfectly well"*) never followed.
> **Predicted severity medium; actual severity invalidated a front-page inference.** Under-severe.

### A5 · Two floor definitions still coexist — `LANDS, narrowly`

R9 emits `floor = sd/|margin|`; R10 and R1 use `2×sd`. R5 was already caught by exactly this and
regenerated its table under both. **Prediction: the adversary finds at least one place where the two
are still mixed within a single comparison.** I have not found one, which is weak evidence of absence
given that I am the person who wrote both.

### A6 · Zero-ablation is off-manifold and the repo cannot resolve it — `RAISED, ALREADY CONCEDED`

R6 returned undecidable, R7 was one family short, R8's separating column was inadmissible
(`randdir`'s positive control sign-inverts). **Prediction: raised; no new information.** If the
adversary shows the floor *reverses* under an on-manifold intervention, that is a genuine kill and I
rate it unlikely but not negligible.

### A7 · `0 unbacked` is weaker than it sounds, **and it gets weaker every time the project grows** — `LANDS, and writing this row found the sharper version`

`make verify` checks that each prose number appears in a reference set of generated values. The
detector measures its own false-pass rate: how often a *random* number of the shape this repository
writes is "backed" by coincidence.

**Predicting this attack is what caught the real problem.** The rate quoted here was `17.2%`,
measured at a reference set of about `500`. One session of additions later the set is over `700` and
the same rate is `24.3%` — **a 41% relative increase in false passes, caused entirely by the
repository succeeding.** Every generator added to strengthen the gate weakens this detector, and
nothing was watching.

It is now measured on **every** `make verify` run and printed under the file table, with a ceiling
that fails the build if it is breached. The ceiling was chosen knowing the present value, so it is
**not** a pre-registration and is not claimed as one — its job is to bound future growth.

**Prediction:** the adversary quotes the false-pass rate back. **It is correct**, and the honest
reading of a clean row is *(1 − that rate)* per number rather than a guarantee.

### A8 · The defect ledger is self-reported — `LANDS`

`67` rows, `35` of them found by the author reading the object, classified by the author, against
bins the author pre-registered. The taxonomy test caught its own designer once; **that is one check, not
independence.** `7` rows came from an outside reader. The cross-tab used to show that **no
instrument had ever caught a `CONTROL` or `SCOPE` defect**; at n=`66` an instrument has caught its
first `CONTROL` one — a false-conviction rule inside the provenance validator, which the validator
surfaced itself. **`SCOPE` is still `0` from instruments against `2` from an outside reader.**

**Prediction:** the adversary says the ledger measures *what the author noticed*, not *what is
there*, and the `10.4%` outside-reader fraction is a floor on the true rate, not an estimate. Correct.

---

## What I predict the adversary will NOT find

Stated so the list can be wrong in both directions:

* **A fabricated or unreproducible number.** After the blockquote exemption was removed, `625` prose
  numbers across `11` files are checked against generated output, and the three that survive
  unbacked are listed by value with a reason in each file's header.
* **A hook that does not do what it claims.** Verified exact on four families, `92` heads, three
  module names, one fused-QKV architecture, residual `5.14e-07` to `7.41e-06`.

  > **⚠ THIS BULLET IS A PROXY STATEMENT AND IT WAS USED IN THE WRONG DIRECTION.** Run the ledger
  > this repository requires of every check:
  >
  > | | |
  > |---|---|
  > | **PROPERTY** | the intervention measures a head's causal contribution |
  > | **PROXY** | the hook zeroes exactly the intended slice, residual `~1e-06` |
  > | **IMPLICATION** | proxy fails ⇒ property fails. **Property fails ⇏ proxy fails.** |
  > | **WITNESS** | `R10_exhaustive/run.py:213` — `x[0, -1, ...]`, the **final position only** |
  >
  > The hook does exactly what its code says and always did. **What it measures is a head's write at
  > the final position**, not a head — its writes at positions `0..n-2` survive, and the layers that
  > can read them number `NL−1−L`, zero at the last layer. Filed as `D83`; it is the reason
  > [R12's verdict is `UNVERIFIED`](R12_cross_model/README.md) and the reason
  > [R18](R18_all_positions/) exists. **The sound direction was used to certify presence**, which is
  > the exact failure this repository's proxy ledger was written to prevent.
* **A verdict quoted without its refusal.** R4, R9 and R10's gates are all refused in place, with
  their numbers still emitted so the refusal itself can be checked.

**If the adversary finds one of these three, the failure is worse than any row above** — it means the
part of the process I trust most is the part that was broken.

---

## SCORED, 2026-07-28 — against the `17` defects found *after* this file was written

This file was written at **`67`** ledger rows and says a row not raised is a miss, and that *"a
finding absent from this list is the most valuable thing"* an adversary can return. The ledger is now
at **`84`**. **So `17` of my own subsequent findings are available to score it, and nobody had.**

| defect | what it was | anticipated? |
|---|---|---|
| `D79` | *"magnitude and role are unrelated"* is an `n=1` relationship claim | **`A1`, exactly** — and `A1` was already marked *ACTED ON*, yet I committed the same error again one step later |
| `D71` | the taxonomy verdict's **reachable set** shrinks as the ledger grows, unwatched | **`A7`, at the level of the class** — *"every generator added to strengthen the gate weakens this detector, and nothing was watching"*. Different instrument, same failure |
| `D76` | R2's task carries R1's fixed-offset degeneracy | **`A2`, partially** — `A2` predicted *"one synthetic task"*; it did not predict the task was degenerate |
| `D68` `D69` `D70` `D72` `D73` `D74` `D75` `D77` `D78` `D80` `D81` `D82` `D83` `D84` | fourteen others | **not on this page in any form** |

```
window                       D68 .. D84        frozen: see below
clean hit                    1 of 17   =  5.8824%
+ class-level and partial    3 of 17   = 17.6471%
```

**The window is frozen, and the first version of this scoring got that wrong.** Scoring *"every
defect found after this file was written"* makes the denominator grow forever, so the hit rate decays
toward zero **without the file getting any worse** — and it moved twice inside a single step, `5.9%`
to `5.6%`, as that same step filed `D85` and `D86`. The estimand that means something is: *of the
defects found between this file's writing and the moment it was scored, how many did it anticipate?*
Rows after `D84` face this file **extended with `A9`–`A13`**, which is a different object.

**Both bounds are reported because the generosity of matching is a choice, and this repository has
already been caught letting a choice like that move a headline by `2.2×`.**

**The honest reading: as a forecast of where defects would appear, this file is between `6%` and
`18%` accurate.** Its value was not in the forecast. It was in `A4`, which the file itself resolved
and scored *"badly — under-severe"*, and in `A7`, whose act of being written found the real problem.
**Writing predictions was productive; the predictions were mostly wrong.** Those are different
claims and only the second one is a failure.

**And `D80` corrects an error inside this file** — see the annotation on `A1`. The scoreboard was
carrying a factual mistake the ledger had already fixed.

---

## Predictions for `R11`–`R18`, which this file did not cover

Written now, before an adversary runs, and before [R18's](R18_all_positions/PREREGISTRATION.md)
result files exist.

### A9 · `×floor` is not portable, and the front page still ranks the eight in it — `LANDS`

[R15](R15_shuffled_scan/) measured the floor as a function of the task's headroom: per-line floors
span `1.66×` and track baseline margin at Spearman `+0.8810`. **So `0.37× the floor` is a statement
about a configuration, not about a head** — and the front page's headline numbers are in that unit.
`R17` showed the *count* survives a lower floor; it did not make the unit portable.

### A10 · Every round after `R10` re-analyses the same result file — `LANDS, and I rank this first`

`R11` `R12` `R16` `R17` and half of `R15` all read `r10_exhaustive_qwen2.5-1.5b.json`. Eight rounds
of findings rest on **one** `16`-minute job. `R11` replicated on disjoint *items* and `R15` on a
shuffled *task*, but **the exhaustive scan itself has never been re-run from scratch on the same
configuration**, so run-to-run variance of the whole pipeline is unmeasured. `input_replication()`
compares R10 against `E132b` and agrees to `3.6e-06` — that is a *cross-implementation* check on
`8` heads, not a *repeat* of `336`.

### A11 · `R17`'s decision not to add a ledger row is discretionary — `LANDS, and it is aimed at something I felt good about`

`R17` attacked a headline claim, found nothing, and wrote *"a pattern caught before shipping is not
a defect in the artifact."* **That rule is applied by the author, to the author's own drafts, with no
written criterion.** An adversary will say the ledger counts what the author chose to file, and that
the `84` is therefore a lower bound with a discretionary boundary — which is `A8` again, one level up.

### A12 · The `R18` kill, stated before its files exist — `I expect it NOT to fire, which is why it is worth stating`

If the head ranking does not survive all-position ablation (`Spearman ≤ 0.3`), *"a head"* and *"a
head's write at the final position"* are different objects and every head-level number here is about
the latter. **I predict it transfers at `≥ 0.7`.** If I am wrong, this row is the record that I was.

### A13 · The centring correction — `MAY LAND, and I do not know`

The null-at-zero defect was found in `R1` and later in `R2` (`D75`). **I have not enumerated every
place a `2×sd` comparison is made.** `A5` predicted the two *floor definitions* would still be mixed
somewhere and I never found an instance; this is the same shape of prediction and I rate it the same.

---

## The prediction I am least confident in

**That A3 is the strongest attack.** I rank it first because it is the one I cannot answer, which is
also exactly the bias this file exists to expose: an author's sense of *"the attack I cannot answer"*
is drawn from the same distribution as the work. The adversary may well lead with something not on
this page at all — and **a finding absent from this list is the most valuable thing it can return.**

---

## SCORED AGAIN, 2026-07-28 — window 2, `A9`–`A13` against `D85`–`D122`

`A9`–`A13` were appended at `D84`. They face a different set of rows than `A1`–`A8` did, so they get
their own frozen window and their own denominator. Scoring them on window 1 would credit predictions
that did not exist when those defects were found.

```
window 1   D68 .. D84   n = 17    clean  5.88%    generous 17.65%
window 2   D85 .. D122  n = 38    clean  2.63%    generous 13.16%
```

**The rate replicates on an independent, larger window.** As a forecast of where defects would
appear, this file is between `2.6%` and `17.7%` accurate. That is now measured twice, not once.

| row | what happened |
|---|---|
| `A13` — *"MAY LAND, and I do not know"* | **the only clean hit.** `D87` is exactly what it described: an unenumerated recurrence of the null-at-zero defect, in `R11`'s rank-stability check |
| `A10` — *"and I rank this first"* | **produced nothing, and got worse.** No row in the window measures pipeline re-run variance, and **three further analyses were built on the same frozen result files inside the window** |
| `A12` — the only numeric forecast | **WRONG.** Predicted the ranking transfers at Spearman `>= 0.7`; observed `0.6230`. The kill (`<= 0.3`) correctly did not fire, so half the forecast held and the point estimate did not |
| `A9` | **acted on before it could be scored** — the third time, after `A1` and `A3` |

### The two things this scoring says, and they point in opposite directions

**Against the file: my ranking of my own weaknesses carries no information.** The prediction I ranked
first returned zero. The prediction I explicitly refused to rate returned the only clean hit. The one
prediction I put a number on was wrong. That is exactly the bias this file was written to expose, and
it has now been measured on two independent windows.

**For the file, and it must be said because it cuts the other way: `A1`, `A3` and `A9` were ACTED ON
before they could be scored.** A prediction that changes the artifact is removed from the denominator.
So both hit rates are **biased downward by the file's own success**, and `2.63%` measures residual
forecast accuracy, *not* the file's value. The value shows up in the repository, where the front page
now leads with *"the single head is the wrong unit"* because `A3` said so.

### One defect in this window was a citation to nothing

`D122` was written into `PAPER.md` as a defect id **before any ledger row existed for it**, and
`make verify` passed — `validate_defects.py` checks commit ancestry, not whether a cited id resolves.
The row is filed now. **The mechanical check is deliberately not added**: `D8`, `D7`, `D6` are also
this repository's *D-level* notation in every commit tag and docstring, so a naive
"every `Dnnn` in prose must exist in the ledger" scan would collide with a second meaning of the same
token. The namespace is overloaded and needs a disambiguation rule before it can be enforced — that
is the finding, and inventing the rule inside a research step is how bad rules get made.

---

## Predictions for `R19`, written before its result file exists

`R19` is running (`layer 19 of 28` at the time of writing). Its four hypotheses and two registered
predictions are in `R19_crossed_position_support/PREREGISTRATION.md` and are **not** repeated here.
These are the attacks I expect on the *analysis*, not the hypotheses.

### A14 · The `64` base instances are not `64` independent items — `LANDS`

Cluster bootstrap over base instances is the right unit only if the bases are exchangeable. They are
generated by one template with rotated room assignments, so between-base variance may be dominated by
which *rooms* a base drew rather than by anything about the base. **The bootstrap will then be
narrower than an honest interval**, in the direction that makes every verdict look sharper.

### A15 · Three metrics, four hypotheses, two arms — and no multiplicity correction is registered — `LANDS`

The pre-registration says *"three metrics reported separately"*, which prevents merging but does not
control the family. With four hypotheses times three metrics there are twelve verdicts, and the
design registers no correction across them. **Reporting separately is not the same as testing
separately.**

### A16 · I predict `H-position` returns UNRESOLVED, not a verdict — `I expect this NOT to be a defect, which is why it is worth stating`

`H-position`'s ICC threshold was chosen at `0.50` in Amendment 1 with no power calculation behind it.
**I predict the observed ICC lands in `[0.2, 0.8]`** — inside the band where `64` bases cannot
separate the hypotheses — **and that the honest verdict is therefore UNRESOLVED.** If it lands
outside that band, this row is the record that I was wrong about my own design's resolution.
