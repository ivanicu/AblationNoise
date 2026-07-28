# Pre-registration — is the reference distribution SCALAR-UP-TO-SCALE?

Written 2026-07-28, **before the statistic was computed**. Committed alone, ahead of the code that
computes it, so that git ordering — not my word — establishes that the thresholds preceded the
numbers.

## The claim under attack

This repository's headline is:

> ablation baselines are conditional distributions, not scalar properties of models.

It has never been attacked. Its deflationary rival has a name and a testable consequence.

| | |
|---|---|
| **World S — scalar-up-to-scale** | each condition's per-head effect vector is *the same shape* times a per-condition scale. The floor is then a scalar property, and the entire conditional apparatus reduces to estimating one nuisance number per condition. |
| **World C — genuinely conditional** | the conditions rank components differently. They are different objects, not the same object in different units. |

## The data — already frozen, no new compute

Four columns on one common index of 336 heads (28 layers x 12), `qwen2.5-1.5b`:

| column | file | axis it varies |
|---|---|---|
| `final/itemsA` | `R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json` | — (reference) |
| `final/itemsB` | `R11_instrument_noise/results/r11_itemsB_qwen2.5-1.5b.json` | item sample (measurement error) |
| `final/shuffled` | `R15_shuffled_scan/results/r15_shuffled_qwen2.5-1.5b.json` | task specificity |
| `all/itemsA` | `R18_all_positions/results/r18_allpos_qwen2.5-1.5b.json` | intervention support |

`r11_itemsA` is byte-identical to `r10_exhaustive` on the cells used here; the A/B pair is the
measurement-error replicate and nothing else.

## The statistic

Columns are mean-centred and standardised, so the test is about **shape**, not scale — precisely the
question that separates S from C. Then:

- `lambda_1 / K` of the K x K correlation matrix. Rank 1 => 1.0.
- the pairwise correlations themselves, reported as absolute values, not only as a summary.

## The strongest confound, written before the run

**Measurement error attenuates every correlation.** A low `corr(final, all)` is exactly what World S
predicts too, if the measurement is noisy enough. The control is already in the matrix and costs
nothing: `corr(final/itemsA, final/itemsB)` differs from 1 **only** by item sampling, so it is the
reliability ceiling that every other pair must be read against.

Disattenuation uses `r_xy / sqrt(r_xx * r_yy)`. Only `r_xx` (final scope) is measured here; there is
no replicate for the `all` or `shuffled` scopes, so substituting `r_yy = 1` yields a **lower bound**
on the disattenuated correlation. That asymmetry is the honest boundary of this test:

- a **high** lower bound is decisive — the shape really is shared;
- a **low** lower bound is **not** decisive, because the unmeasured `r_yy` could be doing the work.

## Registered thresholds

| verdict | rule |
|---|---|
| **CONFIRMED shape-sharing** | lower-bound disattenuated correlation `>= 0.90` |
| **REJECTED** | raw correlation below the 97.5th percentile of the row-permutation null |
| **UNVERIFIED** | anything between — in particular any middling value, because the missing `r_yy` means I cannot place it |

`alpha = 0.05`, `N_PERM = 20000`, seed 20260728.

## Positive controls, run in the same script

The statistic must be shown to move before a value of it is believed.

1. a synthetic rank-1 matrix plus noise must return `lambda_1/K` near 1.0;
2. K independent noise columns must return `lambda_1/K` near `1/K`.

A statistic that has not returned both is not an instrument.

## What each outcome costs me

**If CONFIRMED for the `final` vs `all` pair:** the headline sentence must be narrowed, in the README
and in PAPER.md, to *the floor's SCALE is conditional; its SHAPE over components is not* — and R18's
H-support failure gets reinterpreted as a statement about magnitude, not about which components
matter.

**If REJECTED:** the headline survives its first real attack, and the four axes are established as
carrying non-redundant information rather than assumed to.

## The follow-on this test cannot do

R19 (running, 64 base instances, both scopes) can supply the missing `r_yy`: split the 64 bases into
two halves of 32 and compute a within-scope split-half reliability for `final` **and** `all`. That
converts every lower bound here into a two-sided estimate. Registered now so the analysis is not
invented after seeing this test's outcome.

---

# Amendment 1 — the outcome, and what it converted the rival into

Appended 2026-07-28, after running `condition_shape_rank()`. The thresholds above are unchanged; this
section only records what they returned and the one prediction they generate.

## Verdict, by the rule as written: `UNVERIFIED`

| quantity | band L14-27, 168 heads | all 336 heads |
|---|---|---|
| `lambda_1 / K` | `0.8477` | `0.7381` |
| permutation null, 97.5th | `0.3270` | `0.3053` |
| reliability ceiling `corr(final/itemsA, final/itemsB)` | `0.9942` | `0.9944` |
| decisive pair `corr(final/itemsB, all/itemsA)` | `0.7715` | `0.5061` |
| disattenuated **lower bound** | `0.7737` | `0.5075` |

`0.7737` is below the registered `0.90` and above the null, so by the rule this is the middle case.
**It is recorded as `UNVERIFIED` and not as a rejection.** A false acquittal is permanent, because
nobody re-examines a cleared claim.

The positive controls both returned before any of this was read: synthetic rank-1 gave `0.9891`, four
independent noise columns gave `0.3013` against an asymptotic `0.25` — the excess is finite-`n`
inflation at `n = 336`, and the permutation null lands in the same place, which is the check that the
two agree.

## The decisive pair was chosen by a measurement, not by its name

`shares_items_final_all` is read off the files' `draw_seed` and `n_items`, and it is **true** — so
`final/itemsA` and `all/itemsA` have correlated measurement error and their raw correlation is
inflated. The cross-item pair `final/itemsB vs all/itemsA` is the honest one and is what the verdict
uses. This was written into the design before the run, in the docstring and here, because it biases
in the *unwelcome* direction and would otherwise have been convenient to overlook.

## What `UNVERIFIED` bought: the rival is now one measurable number

The only free parameter left is `r_yy`, the unmeasured reliability of the `all` scope.

```
the data itself floors it                r_yy >= 0.5986     (from r_xy <= sqrt(r_xx * r_yy))
true shape-sharing of 0.90 needs         r_yy <= 0.7390
measured reliability of the FINAL scope           0.9942
```

**World S survives only inside `r_yy` in `[0.5986, 0.7390]`.** That requires the all-position
measurement to be far noisier than the final-query one despite carrying `2.0051x` the spread — which
is a strange thing to be true, but strange is not an argument and it is not being scored as one.

## Registered prediction for R19, before its data exists

R19 runs `64` base instances under both scopes. Split-half reliability, bases `0..31` against
`32..63`, on the band, gives `r_yy` for `all` and re-measures `r_xx` for `final`.

| | |
|---|---|
| **prediction** | `r_yy(all) > 0.7390`, i.e. **outside** the window World S needs |
| **stated confidence** | `0.75` |
| **what it kills if true** | scalar-up-to-scale, as an explanation of the transport failure |
| **what it kills if false** | this repository's conditional framing, which would then be a units error |

If `r_yy` lands **inside** the window, the README block added by this amendment and the headline both
narrow to *the floor's scale is conditional; its shape over components is not*, and R18's H-support
failure is re-read as a magnitude statement. That consequence is written here rather than after the
fact.

## Boundary of everything above

One model (`qwen2.5-1.5b`), one synthetic task, one metric (`signed_margin_drop`), four conditions,
`n = 168` band heads. The `shuffled` arm's reliability is also unmeasured, so its `0.8123` carries the
same one-sided bound and is not used for any verdict.
