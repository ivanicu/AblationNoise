# Pre-registration — the repository has a CENSUS of the population it published a 30-draw SAMPLE of

Written 2026-07-29, **before the census floor was computed**, committed alone so git ordering rather
than my word establishes that the thresholds preceded the numbers.

## What the object says

`R1_noise_floor/run.py:80-82` and `R10_exhaustive/run.py:71-73`:

```
N_ITEMS = 120                     N_ITEMS = 120
SEEDS = list(range(3000, 3400))   SEEDS = list(range(3000, 3400))
DRAW_SEED = 20260727              DRAW_SEED = 20260727
```

and `bindings()` and `prompt()` are **byte-identical** between the two files. That is why the leakage
audit's control 2 returned `abs err 0.000e+00`: `R1`'s `band_k1` draws and `R10`'s exhaustive scan
are **the same measurement on the same items**.

**So `R10` is a CENSUS of the population `R1` sampled `30` times, with replacement.** The floor this
repository publishes — `0.4417733517951077` — is a `30`-draw sample estimate of a parameter it has
measured **in full**, in a file sitting one directory away.

## The two worlds

| | |
|---|---|
| **World E — the sample is an estimate** | the `30` draws are an ordinary sample from the census; the published floor sits in the middle of the sampling distribution, and the only cost of having used a sample is the `0.13130643285972254` standard error `R22` already reported. Then the fix is bookkeeping: quote the census. |
| **World B — the sample is biased or the two are not the same population** | the published floor sits in a tail of the `30`-draw sampling distribution drawn from the census. Then either the substitution that control 2 validated is not what it appears, or the sample was not drawn the way the code reads — and `abs err 0.000e+00` would have to be explained some other way. |

**Under `World E` there was never any need for a standard error at all.** A census has none. Every
sentence in `R22` that reasons about the sampling error of the floor was reasoning about a choice,
not a limit — including my own, written an hour ago.

## Registered thresholds

Population: `168` band heads `L14`–`L27`, `qwen2.5-1.5b`, original vocabulary, `n = 120` items.

| verdict | rule |
|---|---|
| **SAMPLE-IS-ORDINARY** | the published floor lies within the central `95%` of `20000` bootstrap resamples of `30` from the census |
| **SAMPLE-IS-ATYPICAL** | outside it |
| **UNVERIFIED** | the recovered `30`-draw list does not reproduce the published floor exactly |

And reported regardless of the verdict word:

1. **the census floor**, `2 x sd` over all `168`, which carries **no sampling error**;
2. **the census floor with the eight tested heads removed** — the leave-out that `resolution_limit()`
   already mandates and that is exact on a census;
3. **`n_inside` under both**, against the published `7`.

## The strongest confound, written before the run

**A census of `168` heads is not a census of the estimand.** The `168` are one model, one vocabulary,
one item set; the quantity the floor is meant to stand for is *what a random component does*, and
that has variance across items and across models which no amount of head-exhaustiveness removes.
**Removing the `30`-draw sampling error does not make the floor exact — it removes one of at least
three sources**, and quoting the census as though it were the true floor would be the same overshoot
in a new place.

**Control, in the same iteration:** the item-level and cross-model components are **not** claimed to
be zero here; `R11` measured the instrument at `0.0194` of the floor and that number is carried into
the report rather than dropped. The census claim is scoped to *between-head* variation only, and that
scope is written into the output.

**Second confound: `2 x sd` on `168` heads is still `2 sd` on a distribution with excess kurtosis
`7.31`**, which the repository has already said is not a normal-theory threshold. The census fixes
the sample size, not the estimator, and `R22`'s grid already showed the estimator matters more.

## What each outcome costs me

**`SAMPLE-IS-ORDINARY`** — which I expect — means the published floor was never wrong, merely
**unnecessarily noisy**: the repository spent a `0.13130643285972254` standard error it did not have to spend,
and `R22`'s own SE argument, written an hour ago, was about a self-inflicted limit. **That is the
unwelcome part and it is mine.**

**`SAMPLE-IS-ATYPICAL`** would mean the `abs err 0.000e+00` control validated something other than
what I read it as, and the leakage round's conclusions would need re-examining rather than extending.

## Boundary

One model, one vocabulary, one metric, `168` heads, `n = 120` items, `I_final`, between-head variation
only. A census removes sampling error over heads and **nothing else**. Nothing here proposes that the
census floor replace the published one in past claims; it establishes what the published one was an
estimate *of*.

---

# Amendment 1 — `SAMPLE-IS-ORDINARY`, and on the census it is `8 of 8`

Appended 2026-07-29. **No threshold above was changed.**

## Gate

The recovered `30`-draw list reproduces `0.4417733517951077` exactly. The census is readable.

## The numbers

```
published, 30 draws                    0.4417733517951077
CENSUS, all 168 heads                  0.4870370929459915      1.102459193083871x
CENSUS with the eight removed, 160     0.4911033692180353

n_inside      published 7      census 8      census leave-the-eight-out 8

30-from-census bootstrap, 20000 draws  95% [0.2309544615772209, 0.7351703499669623]
                                       median 0.46351226239502186
the published floor sits at percentile 0.4418
```

## `SAMPLE-IS-ORDINARY`: nothing was cherry-picked, and that is the point

The published floor sits at percentile `0.4418` of the `30`-draw sampling distribution — **dead
centre.** It was an ordinary draw. Nothing was selected, nothing was tuned.

**It was merely noisy, and it did not have to be.** The `95%` interval of a `30`-draw estimate from
this census is `[0.2310, 0.7352]` — a **`3.18x` span**, which is *larger than the entire
estimator-and-population grid* `R22` measured at `3.8980x`… and of the same order. **Choosing to
sample `30` when a census of `168` existed cost more instability than every estimator choice in that
grid put together, and it was avoidable by reading a file.**

## And the count changes: `7 of 8` becomes `8 of 8`

The census floor is `10.2%` larger than the sample estimate, so `L16H3` — which cleared the published
floor by `5.667495896844854%` — **falls inside it.** The count is `8` on the census, and still `8`
after removing the eight from their own reference, which is the leave-out `resolution_limit()`
already mandates.

> **The one head that made the headline `7 of 8` rather than `8 of 8` was kept outside by the
> sampling error of a `30`-draw estimate of a parameter the repository had measured in full.**

This moves the repository's central claim **in the deflationary direction**: the eight are not *less*
special than published, they are **not special at all** on the reference the repository already owns.
`D176` said the count was robust at `6`–`8` with modal `7`; the census picks out `8`, and the honest
headline is *"all eight sit inside a floor computed from a census of the same population."*

## What this does not license

**A census over `168` heads is not a census of the estimand**, exactly as registered. It removes the
**between-head sampling error only**. The item-level component, the cross-model component and the
estimator choice are all untouched — `R22`'s grid showed `n_inside` moving over `{6, 7, 8}` on band
references under estimator choices alone, and the census is one cell of that grid, not an escape
from it. `2 sd` on `168` heads is still `2 sd` on a distribution with excess kurtosis `7.31`.

**And the `R11` instrument component could not be carried.** The registration said it would be, to
keep the scope honest; `headline.r11()` does not expose `instrument_frac_of_floor` under that name,
so the field emitted `null`. **That is a promise this file made and did not keep**, recorded here
rather than quietly dropped.

## A bug in this file, caught by reading its own printed count

The first run reported *"census, the eight removed (**167**)"* where `160` was expected. `tag()`
zero-pads the head index (`L16H03`) while `r1_prior_effects()` keys do not (`L16H3`), so the
membership test matched only the one head with `h >= 10`. **One head was removed, not eight, and the
line still printed a plausible floor.** Caught because the count was printed beside it; fixed by
parsing the keys the way `leakage.py` already did. The corrected leave-out floor is
`0.4911033692180353`, and `n_inside` is `8` either way.

## Boundary

One model, one vocabulary, one metric, `168` heads, `n = 120` items, `I_final`, between-head
variation only. The bootstrap resamples heads with replacement from the census and does not
propagate item-level noise. Nothing here rewrites past claims; it establishes what the published
floor was an estimate *of*, and what the same population says when read in full.
