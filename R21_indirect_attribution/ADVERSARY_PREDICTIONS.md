# Pre-registration — what I predict an adversary will find in `R21`, written before one is dispatched

Written 2026-07-29, **before the reviewer is briefed**, committed alone so git ordering rather than
my word establishes that the predictions preceded the findings.

## Why this is the experiment and not bookkeeping

Two hours ago an independent reviewer moved **five of `R20`'s six claims down a bucket**, and every
recomputation reproduced. One step later I found `D157` — a tautological control — **by reading my
own code.** Those two facts point at different worlds about *me as an instrument*, and no further
result about the model separates them:

| | |
|---|---|
| **World C — calibrated** | I now know my failure classes, and knowing them lets me find them in my own work. `D157` is a point for `C`. Then self-review is *weak*, and a checklist recovers most of it. |
| **World B — blind** | knowing the classes does not transfer to my own material; what I catch is the subset I happened to look at, and the rest needs an outsider. `R20`'s nine findings are a point for `B`. Then **self-review is void in the strong sense** and the adversary is not optional at any budget. |

**The discriminating action is free**: write the predictions, dispatch, score. It costs one agent and
its worst outcome still forces a large update, because a low hit rate would mean every unreviewed
round in this repository is worth less than its page implies.

## The registered scoring rule

A prediction is a **HIT** only if the adversary's finding names **the same statistic AND the same
defect mechanism**. Naming the same statistic for a different reason is a **NEAR MISS** and scores
zero — partial credit is where narratives live.

```
recall    = HITS / (adversary's CONFIRMED findings)     <- the number that matters
precision = HITS / (my predictions)
```

**Recall is the test.** Precision only measures whether I can generate plausible-sounding defects,
which is a skill I have already demonstrated by generating the defects in the first place.

| verdict | rule |
|---|---|
| **CALIBRATED** | recall `>= 0.50` **and** precision `>= 0.50` |
| **BLIND** | recall `< 0.25` |
| **MIXED** | anything else |

**Meta-prediction, scored separately:** at least one of the adversary's findings will be in a class
**already filed in this repository's own ledger**. `R20` and `R21` each repeated a class the other
had just recorded, so I expect a third repeat.

## The predictions, ranked by how sure I am

| # | statistic | the defect I predict |
|---|---|---|
| **P1** | `NORM 0.1706` | **the split is not unique.** `k'v' - kv` can be written `k'(v'-v) + (k'-k)v` or `k(v'-v) + (k'-k)v'`; `run.py` uses the first without saying that the second exists. `NORM`'s share is convention-dependent and the page presents it as measured. **This is the one I most expect and I could not talk myself out of it.** |
| **P2** | `att_late` "equals `ATT` to `3e-10`" | **a second tautology.** Heads at or before the ablated layer read an unchanged input, so their writes *cannot* move; `datt[:L+1]` is exactly zero by physics, and the check reports arithmetic as a structural finding. Same class as `D157`, one row down the same table. |
| **P3** | `ratio_total_over_own 3.8417x` | **it is compared on the page against `R20`'s `3.3251x`, which is retracted** — an order statistic on an even `n`, honest per-head value `1.8960x`. A live comparison against a withdrawn number. |
| **P4** | `Spearman(OWN, R20 direct) +0.9068` | **a threshold squeak against a registered `0.90`**, and the thing it is validated against is itself under retraction. `0.0068` of margin is not a control passing, it is a control not quite failing. |
| **P5** | the `44` comparator-stable heads | **selected on a covariate that is not independent of the outcome.** A flip rate of exactly `0` plausibly marks the *low-effect* heads, so the subgroup that rescues the control may be the subgroup with the least to measure. Disclosed as post hoc; **not** disclosed as possibly confounded with effect size. |
| **P6** | `median share` | **median-of-shares is not share-of-medians**, and `|class| / SUM |class|` discards sign, so a class whose contributions oppose each other across heads still scores a large share. The verdict word rides on a statistic that is not the quantity the sentence describes. |
| **P7** | `cancellation 0.1734 / 0.1392` | **the denominator can approach zero**, and no floor is registered; the median hides how many heads sit near it. |
| **P8** | R21's numbers | **never entered into the `A18` multiplicity family**, one round after that family was built. A repeat of `D156`'s ninth item. |

## What I expect to be WRONG about

**I expect the adversary to find something in the `MLP` class that I have not thought about at all.**
Every prediction above is about a convention, a tautology, or a population — the shapes I have been
burned by this session. `MLP 0.2341` and its `per member 0.001698` are the numbers I have inspected
least, and the pattern of the last two rounds is that the finding arrives where I did not look.

**If that is what happens, it is evidence for World B**: the classes I know are the classes I check,
and the ones I do not know are exactly the ones an outsider is for.

## Boundary

One reviewer, one round, one prompt. A single adversary's coverage is itself a sample — a miss is
not proof I was right, and this scores *my prediction against its findings*, not against the truth.
`n = 1` on the calibration question; `R20`'s round is the only prior, and it was unpredicted because
I registered nothing before dispatching it. **That omission is why this file exists.**

---

# Amendment 1 — the score

Appended 2026-07-29 after the reviewer returned **`9` CONFIRMED findings**. It confirms it did not
open this file. **No threshold above was changed.**

## Prediction by prediction

| # | what I predicted | what came back | |
|---|---|---|---|
| **P1** | `NORM`'s split is convention-dependent (`k'(v'-v)+(k'-k)v` vs the mirror) | it tested exactly that pair and **OVERTURNED** it — median share moves `1.3%`, `0.1706`, a shift the reviewer measured at about one part in eighty. It then found a *different* non-uniqueness: a fourth split with **no `NORM` class at all**, `SUM_c (k'v'_c - k v_c)`, under which `NORM` is `0` by construction. Same statistic, **different mechanism** | **MISS** |
| **P2** | `att_late == ATT` is a second tautology | *"it is float rounding of an identity, not a measurement… the gate is applied only at `L27`, where the slice is empty. **The check cannot fail.**"* | **HIT** |
| **P3** | the page compares `3.8417x` against `R20`'s retracted `3.3251x` | *"the parenthetical should read `1.8960x`"* | **HIT** |
| **P4** | Spearman `+0.9068` clears `0.90` by `0.0068`, against a quantity under retraction | confirmed **and gone further**: `Spearman(OWN, direct_linear) = 0.9998810493974013` — **`OWN` *is* `direct_linear`**, so the control measures `R20` against itself, and `0.0068` of margin is smaller than `R20`'s own internal convention gap | **HIT** |
| **P5** | the `44`-head subgroup may be confounded with effect size | `Spearman(flip_rate, |own|) = +0.5762`, stable heads have **`3.2x` smaller `|own|`**, Mann-Whitney `p = 6.1322e-08` — **and beyond my prediction**, a depth-matched null puts the `0.5294` at its **`20`th percentile**, so the subgroup is *less* attention-dominated than chance | **HIT** |
| **P6** | median-of-shares is not share-of-medians; the share discards sign | both halves, with numbers: the four shares **sum to `0.8892`**, and the median *signed* shares are `ATT +0.1393 / MLP +0.0513 / **NORM −0.0625**` | **HIT** |
| **P7** | the cancellation denominator has no floor; the median hides the distribution | the distribution half confirmed (`18x` range, `p10 0.0216` to `max 0.8158`). But the mechanism it found is sharper and **not mine**: the factor pools within-class cancellation with **across-item sign flipping**, proved by a **one-member** class at `L27` reporting `0.672` — with one member there is nothing to cancel against | **NEAR MISS — scores zero** |
| **P8** | `R21` never entered the `A18` multiplicity family | not raised | **MISS** |

## The registered score

```
adversary CONFIRMED findings                    9
of those, predicted by a HIT                    5     (its items 1, 2, 5, 6, 8)
recall     5 of 9            >= 0.50
precision  5/8 = 0.6250        >= 0.50
```

**Registered verdict: `CALIBRATED`.**

## And the rule I registered flatters me

**Recall counts findings. It does not weigh them, and the reviewer's findings are not the same size.**

- Its **most severe** result is that **all three surviving controls are tautologies — the round has
  zero non-trivial controls left**, and *"nothing in the round checks the `OWN`/`ATT` boundary or the
  `ATT`-vs-`MLP` class assignment — the two partitions the entire result consists of."* I predicted
  two thirds of that (`P2`, `P4`) and never saw the conclusion.
- Its **largest numeric corrections** are ones I did not predict at all: both member counts count
  components that **cannot contribute** (live members are `(27-L)*12` and `28-L`, so `ATT` per-member
  is wrong by `7.5x`, `MLP` by `3.7x`, and *"`10x` more per member"* is **`4.97x`**); and `NORM`
  measured against the indirect term rather than `SUM|class|` is `0.3033`, not `0.1706`, exceeding
  the entire indirect term on `39` of `168` heads.

> **`CALIBRATED` by my own rule, and the rule is a count.** Weighted by how much each finding moves a
> number, I did substantially worse than `5/9` — and I wrote the rule.

## The meta-prediction, and the thing I registered expecting to be wrong

**Meta-prediction — CONFIRMED three times over.** *"At least one finding will be in a class already
in this repository's ledger"*: the tautological control is `D157`'s class, the low-signal-selection is
`D151`'s, the retracted anchor is `D155`'s.

**And the sentence I registered under *"what I expect to be WRONG about"*:**

> *"I expect the adversary to find something in the `MLP` class that I have not thought about at all…
> `MLP 0.2341` and its `per member 0.001698` are the numbers I have inspected least, and the pattern
> of the last two rounds is that the finding arrives where I did not look."*

**It did, and it was `0.001698` itself** — the exact number I named — wrong by `3.7x` because the
denominator counts `28` MLPs when at most `28-L` can contribute.

## What this settles about the two worlds

**World C survives on the registered rule; World B survives on severity, and I cannot separate them
with `n = 1`.** What is not ambiguous:

> **The classes I know are the classes I check.** Five of eight predictions landed, and every one was
> a shape I had been burned by *earlier the same day*. The findings I missed were about live-member
> counts, a denominator choice, and a depth composition — none of which is on my scar list. **A
> checklist recovers the failures already on it and nothing else, which is exactly the argument for
> an outsider at every round rather than at the end.**

## Boundary

`n = 1` reviewer, `n = 1` round, one prompt. A single adversary's coverage is a sample: its `9` are
not *the* defects, only the ones it found, so recall is measured against a moving denominator. The
prompt named seven attack surfaces and the reviewer's findings cluster on them — **I wrote the
prompt, so part of what it found is what I pointed it at**, which inflates recall and is not
corrected for here.
