# Pre-registration — is this repository's CENTRAL number identified, or is it one cell of a surface nobody computed?

Written 2026-07-29, **before the grid was computed**, committed alone so git ordering rather than my
word establishes that the thresholds preceded the numbers.

## What R21 opened, and why it is not about R21

`R21`'s class share moved from `0.3734` to `1.0421` across `24` defensible population × denominator
cells, with the registered threshold **inside** that range. The verdict was withdrawn: the quantity is
not identified.

**That question has never been asked of any other round.** Every headline in this repository is a
single cell of a surface nobody computed — including the one the whole project is named for.

## The claim under attack is the central one

`headline.r1_prior_effects()`:

```
floor_2sd_same_vocabulary   0.4417733517951077
n_inside                    7  of  8
largest                     L16H3, clears the floor by 5.667495896844854 %
```

**Seven of eight published single-head effects sit inside the floor.** It is the sentence the
repository exists to deliver, and the whole count turns on one head that clears by `5.67%`.

## The arithmetic that makes this worth running, before anything is computed

The floor is `2 x sd` of **`30`** random single-head draws. The standard error of an sd on `n = 30`
is about `sd / sqrt(2(n-1)) = sd / 7.62`, i.e. **`13.1%` of the floor.**

> **The sampling error on the floor is `2.3x` larger than the margin by which the count is decided.**

So `8 of 8` and `7 of 8` are both inside one standard error of the same experiment — before any
analysis choice is varied. That is arithmetic on two published numbers and needed no new run.

## The two worlds, and they are about this repository rather than the model

| | |
|---|---|
| **World I — R21 was special** | a *share* is a ratio of parts to a whole, and the whole is a convention, so it was uniquely exposed. Counts, standard deviations and correlations have no such freedom, and the rest of the repository's headlines are identified. |
| **World G — general** | every statistic here rests on analysis choices nobody justified, and the headlines move comparably under them. Then this repository is a collection of one-cell readings from uncomputed surfaces — **which is precisely the charge it lays against `E132b`**, and it would have been committing it throughout. |

## The gauge test, which is the whole design

Name the transformations that leave the **model** identical and change the **measurement**:

```
scale estimator   sd(ddof=1) | sd(ddof=0) | MAD x 1.4826 | IQR / 1.349 | 10% trimmed sd
multiplier        2 | 1.96 | the empirical 95th percentile | the empirical 97.5th
reference draw    the registered 30 k=1 band draws | all 168 exhaustive band heads | the sham band
centring          raw | centred on the reference mean
```

None of these touches the network. **If `n_inside` moves across them, `7 of 8` is a property of my
analysis and not of the model** — and the repository has already said, of its own floor, that `2 sd`
is not a normal-theory threshold at excess kurtosis `7.31`, which makes the multiplier row contested
by the project's own admission.

## Registered thresholds

Population: the `8` heads `E132b` measured, `qwen2.5-1.5b`, original vocabulary, `n = 120` items.

| verdict | rule |
|---|---|
| **IDENTIFIED** | `n_inside` takes **one** value across the grid |
| **NOT-IDENTIFIED** | `>= 3` distinct values, **or** the modal value covers `< 50%` of cells |
| **MIXED** | between |

And reported regardless of the verdict word:

1. **the bootstrap standard error of the floor itself**, resampling the reference draws, against the
   `5.667495896844854 %` margin that decides the count;
2. **the number of DISTINCT values of `n_inside`**, which is insensitive to how many near-duplicate
   cells the grid happens to contain.

## The strongest confound, written before the run

**Grid cells are not independent, and I choose how many there are.** `2` and `1.96` differ by `2%`;
`sd(ddof=0)` and `sd(ddof=1)` by `1.7%` at `n = 30`. Packing the grid with near-duplicates would push
the modal fraction toward `1` and manufacture `IDENTIFIED`; packing it with exotica would manufacture
the opposite.

**Control, in the same iteration:** the **distinct-value count** is the primary reading and it is
immune to cell multiplicity, and a **core grid** is reported separately, containing only the three
choices the repository has *already* flagged as contested in its own pages — the `2 sigma` multiplier
at kurtosis `7.31`, the band boundary, and a robust scale for a heavy-tailed distribution. If core
and full disagree, the core is the one to read and that is stated now rather than after.

**Second confound: the reference draw is not a free choice.** The published floor comes from `30`
draws in the *original* vocabulary; the exhaustive `168` come from a later run. Substituting them
changes the vocabulary and the item set as well as the estimator, so that row is a **bundle** and is
reported as one — not as evidence about the estimator.

## Positive control

At the registered configuration — `sd(ddof=1)`, multiplier `2`, the `30` `k=1` band draws, raw — the
tool must reproduce `0.4417733517951077` and `n_inside = 7` **exactly**. A grid that cannot land on
the published cell is not measuring the published quantity, and no other row is readable.

## What each outcome costs me

**`NOT-IDENTIFIED`** is the expensive one and I expect it: the headline becomes *"between `k` and `m`
of the eight, depending on choices the pre-registration never justified"*, and **every downstream
sentence resting on `7 of 8` inherits that**. It would also mean this repository has been reporting
one-cell readings while telling other people not to.

**`IDENTIFIED`** would say the floor is robust where the share was not, and would confine `R21`'s
problem to ratio statistics — which is the outcome that costs the least and is therefore the one to
distrust.

## Boundary

One model, one vocabulary, one metric, `8` heads, `n = 120` items. This is about whether the
published count survives analysis choices — it is **not** a claim that any particular cell is the
right one, and nothing here selects a replacement value. The bootstrap SE is on the `30` reference
draws only and does not propagate the item-level noise inside each draw.
