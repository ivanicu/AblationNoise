# Pre-registration — is adversarial review measuring the artifact, or the prompt I wrote for it?

Written 2026-07-29, **before either agent is dispatched**, committed alone so git ordering rather
than my word establishes that the thresholds preceded the findings.

## The gap this opens

The last round scored my predictions against a reviewer's `9` findings and returned `CALIBRATED`.
Its own boundary says why that is not settled:

> *"The prompt named seven attack surfaces and the reviewer's findings cluster on them — **I wrote
> the prompt, so part of what it found is what I pointed it at**, which inflates recall and is not
> corrected for here."*

**So the calibration score is confounded with my own choice of where to point.** Every adversarial
review in this repository has run on a brief I wrote. If the findings are largely a function of the
brief, then *"an independent reviewer confirmed it"* means less than the page implies — and the
`38` `outside_reader` rows in the ledger inherit that.

## The two worlds, and they differ in what a review IS

| | |
|---|---|
| **World S — surface-driven** | the defects are in the artifact. A competent attacker finds them however it is briefed, because they are what is wrong. Then one review is close to sufficient and the brief is a formality. |
| **World P — prompt-driven** | the findings are largely a function of where the brief points. Then a single review measures **the briefer's imagination**, not the artifact, and *"reviewed"* is a claim about me. **Every `outside_reader` row in this repository would need that qualifier.** |

These are not two values of a parameter. They differ in whether a review is evidence about the work
or evidence about the person who commissioned it.

## The discriminating action: a brief I do not write

Two agents, dispatched by me, neither spawning:

1. **The briefer.** Reads `R21` cold and writes an attack brief — which surfaces to hit and why. It
   attacks nothing. **It never sees my prompt, my predictions, or the first review.**
2. **The attacker.** Receives the briefer's text **verbatim** as its instructions, plus the target.
   Same prohibitions.

Then the overlap between the attacker's findings and the first review's `D159`–`D167` is the
statistic.

## Registered thresholds

A finding **MATCHES** a ledger row only if it names the same statistic **and** the same defect
mechanism — the same rule the last round used on my own predictions, so the two scores are
comparable.

```
overlap = MATCHES / (the attacker's CONFIRMED findings)
novel   = findings matching neither D159-D167 nor my eight registered predictions
```

| verdict | rule |
|---|---|
| **SURFACE-DRIVEN** | overlap `>= 0.50` |
| **PROMPT-DRIVEN** | overlap `< 0.25` |
| **MIXED** | between |

And reported regardless of the verdict word: **`novel`** — what a second independent pass buys after
the first has run. If `novel` is large under *either* verdict, one review is not enough and this
repository's `9`-finding rounds were floors, not audits.

## The strongest confound, written before the run

**Both agents will read the same `README.md`, and that file now CONTAINS the first review's
findings** — the `D159`–`D167` retraction block sits directly under the `R21` section. If either
reads it, the overlap is manufactured and the experiment is void.

**Control, in the same iteration:** both agents are explicitly forbidden
`R21_indirect_attribution/ADVERSARY_PREDICTIONS.md`, `R21_indirect_attribution/tools/adversary_recompute.py`,
`R21_indirect_attribution/results/r21_adversary_recompute.json`, `defects.json`, `DEFECT_LEDGER.md`,
and the `README.md` block beginning *"RETRACTED, `D159`"*. **Each is required to list the files it
actually read**, and a run that opened a forbidden file is reported as `VOID`, not scored.

**Second confound: the attacker's coverage is bounded by the briefer's imagination.** Low overlap
could mean *"the brief pointed elsewhere"* rather than *"the first review was prompt-driven"* — which
would be a fact about one agent, not about review. Controlled only partially: the briefer is asked
to be comprehensive about surfaces rather than selective, and **its brief is published verbatim**
so a reader can see what it chose to point at. `n = 1` briefer, and that is stated as the limit.

**Third: the first reviewer's prompt named seven surfaces and it returned nine findings**, so it
went beyond the brief at least twice. A high overlap therefore does not prove briefs are irrelevant
— only that these particular defects survive a change of brief.

## What each outcome costs me

**`PROMPT-DRIVEN`** is the expensive one and I would find it unwelcome: every *"an independent
adversarial reviewer returned this, CONFIRMED"* in this repository — `38` ledger rows — would need
to read *"a reviewer I briefed, on surfaces I chose"*. It would also mean the calibration score of
the last round is not a measure of my blind spots but of my aim.

**`SURFACE-DRIVEN`** says the defects were simply there, which strengthens the first review and
weakens nothing except the assumption that briefing is hard.

**A large `novel` count under either verdict** is the outcome that costs the most in work: it would
mean `R21`'s nine findings were a sample, not a census, and that the honest label on every reviewed
round is *"at least this many"*.

## Boundary

`n = 1` briefer, `n = 1` attacker, one round, one artifact. Both agents are drawn from the same
model family as me, so this measures whether a *different context* changes what is found, **not**
whether a different mind would. A human reviewer is not tested here and nothing below generalises to
one. Matching is judged by me, which is the same person whose calibration is under test — the
matches are published finding-by-finding so that judgement is checkable.

---

# Amendment 1 — the registered control FAILED, and the score is reported as a post-hoc reading

Appended 2026-07-29. **No threshold above was changed.**

## The forbidden-file control fired, and the attacker fired it on itself

The registered rule: *"a run that opened a forbidden file is reported as `VOID`, not scored."* The
attacker's own scope statement:

> *"a `grep -n "3.8417\|convention" README.md` returned four match lines from inside the forbidden
> region (617, 643, 646, 647). I read the grep output before I could suppress it… Overlap with the
> `D159`–`D167` block is possible throughout and **I cannot bound it**."*

**Registered verdict: `VOID`.** It did not open the file, but it saw four lines of it, and the rule
does not have a partial branch — **because I did not write one, which is the defect.** A control with
two states cannot describe a three-state world, and this is the fourth registered control in three
rounds that could not express what actually happened.

**Everything below is therefore a post-hoc reading and is labelled as one.** The breach direction is
knowable and it is unfavourable: seeing the first review's findings can only **raise** overlap, so
the number below is an **upper bound** on the true overlap and the verdict it implies is the one the
breach favours.

## The briefer's control passed cleanly

Its `FILES READ` line lists `38` paths, none forbidden, and it **never opened `README.md` at all**.
So the brief itself — published verbatim at [`SECOND_REVIEW_BRIEF.md`](SECOND_REVIEW_BRIEF.md) — is
uncontaminated. That is the half of the experiment that survives.

## The score, finding by finding, so the matching is checkable

| # | the attacker's finding | matches | |
|---|---|---|---|
| 1 | `analyze.py` drops the failed control out of its own gate; the registered verdict is `UNVERIFIED` | — | **NEW** |
| 2 | `MIXED` survives `2` of `24` population × denominator cells; the signed denominator makes ATT the top class outright | `D165` | match |
| 3 | under the repository's **own** floor convention `131 of 168` heads are below floor, not `64` | — | **NEW** |
| 4 | `EMB` is blind to **misclassification**; only deletion is caught | `D159` | match |
| 5 | control 3 runs against `direct_renorm` while `OWN` **is** `direct_linear` (`+0.9999`) | `D159` | match |
| 6 | the *"difference is the comparator convention"* explanation is **OVERTURNED** — both rounds use the same comparator | — | **NEW**, and it corrects `D163`'s framing |
| 7 | `R21` dropped **six** refusal gates, not three, including one it had the data to run free | — | **NEW** |
| 8 | cancellation conflates two axes; the null is `1/sqrt(n)`, not the brief's formula | `D161` | match |
| 9 | `att == att_late` is a theorem; two controls test `0.0 < 1e-6` | `D159` | match |
| 10 | membership counts include components that cannot move | `D162` | match |
| 11 | the motivating premise is a number from a run whose own verdict is `UNVERIFIED` | `D163` | match |
| 12 | the P7 plant's planted arm has **no checked-in artifact**, and the script's default `--out` is the published artifact's path | — | **NEW** |
| 13 | the `44`-head repair explains `23%` of the variance it is offered to explain | `D160` | match |
| 14 | sweep: the unregistered `1e-4`, the README's ordering, plus a `240`-candidate cap and an `n<30` gate | `D167` | match |

```
attacker CONFIRMED findings          13
matching a D159-D167 row              9
overlap  9 of 13             >= 0.50     -> SURFACE-DRIVEN, as a post-hoc reading
novel (neither ledger nor my eight predictions)   5
```

## What this says, at the size it supports

**`SURFACE-DRIVEN`, upper-bounded.** Nine of thirteen findings survived a change of briefer, and the
briefer never saw the first review. So the defects are substantially **in the artifact**, and
*"an independent reviewer confirmed it"* is not merely a claim about who wrote the prompt.

**And the number that matters more is `novel = 5`.** A second pass over an already-reviewed round
found five things the first missed — including that **`analyze.py` dropped the failed control out of
its own gate**, which makes the registered verdict `UNVERIFIED` rather than `MIXED`, and which two
reviews and an author had all walked past. **One review is a floor, not a census.** Every reviewed
round in this repository should read *"at least this many"*.

**The one thing the second review could not have inherited from mine, it found first**: the brief was
written by an agent that had read the code and nothing else, and its rank-1 surface — *the verdict is
a choice of denominator* — is the one that flips the headline. **A reader who has only the artifact
outranks a reader who has my questions.**

## Boundary

`n = 1` briefer, `n = 1` attacker, one round. Both are the same model family as me, so this measures
whether a *different context* changes what is found, not whether a different mind would. Matching was
judged by me and is published row by row above so the judgement is checkable. The overlap is an upper
bound for the disclosed breach, and the `VOID` verdict stands as the registered outcome.
