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
