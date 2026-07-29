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
