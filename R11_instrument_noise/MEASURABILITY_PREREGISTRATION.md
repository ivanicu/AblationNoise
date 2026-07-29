<!-- unbacked-ok: 1.96 -- the two-sided normal quantile of the SUPERSEDED Bland-Altman design.
 Amendment 1 replaced that design before it ran, so no generator emits this constant and none should:
 it is kept because the abandoned design is kept, and a design deleted after being committed is a
 record destroyed rather than corrected. -->
# Pre-registration — the direct measurement `item_noise_bound()` said would need a re-run

Written 2026-07-28, **before the statistic was computed**, committed alone so git ordering rather than
my word establishes the thresholds preceded the numbers.

## The live `UNVERIFIED` this closes

`headline.py :: item_noise_bound()` was retracted one step after it was published. Its retraction
says, verbatim:

> **THE DIRECT TEST IS NOW THE ONLY ROUTE, and it is cheap: re-run the same heads on a DISJOINT item
> set and store `sd_over_items/sqrt(n)` per head. The runner already computes the per-item drops and
> throws them away.**

**That re-run already exists and has been in this repository since R11.** `r11_itemsA` (seeds
`3000`–`3400`) and `r11_itemsB` (seeds `3400`–`3800`) are the same heads, the same model, the same
deterministic intervention, differing in **nothing but the item sample**. So `A_h − B_h` is a direct
draw from the instrument's own error distribution, per head, with no GPU and no new experiment.

The claim being repaired is the `measurable` column and `n_measurable`, currently `UNVERIFIED`:
its old threshold was twice a *quiet-layer* bound, which the retraction showed has no established
relation to the item noise of a live head.

## The two estimands the phrase "inside the noise floor" conflates

| | |
|---|---|
| **NOT MEASURABLE** | the effect is below the instrument's precision — a statement about noise |
| **NOT DISTINCTIVE** | the effect is real but indistinguishable from a random component of the same size — a statement about the reference population |

Only the second has ever been measured here. This test measures the first.

## Statistic

For each of the 336 heads, the Bland–Altman pairing:

```
mean_h  = (A_h + B_h) / 2          the effect-size estimate
diff_h  =  A_h - B_h               a draw from the error distribution
sigma_h ~ sd of diff, estimated in bins of |mean_h|, divided by sqrt(2)
```

**The pairing is mean-vs-difference and not arm-vs-difference on purpose.** Binning by `A` and then
plotting `A − B` induces a correlation by construction — regression to the mean wearing the mask of
heteroscedasticity. That is the strongest confound here and its control is the pairing itself.

## The claim under test

The retraction asserted that item noise **is not constant across heads** — that a quiet head is quiet
in both its effect and its item-to-item variance — and used that to kill the bound. It asserted this
from a layer-level Spearman of `+0.962` between a layer's mean `|drop|` and its spread, which is a
statement about **between-head spread**, not about **measurement error**. This test measures the
error term directly.

| verdict | rule |
|---|---|
| **CONFIRMED** — noise scales with effect | `Spearman(|mean_h|, |diff_h|)` over 336 heads `>= 0.50` |
| **OVER-RETRACTED** — noise roughly constant | `<= 0.20` **and** the bootstrap CI excludes `0.50` |
| **UNVERIFIED** | anything between |

`alpha = 0.05`, `N_BOOT = 10000`, seed `20260728`.

## Positive controls, in the same script

A difference-based instrument that has never been shown to move is silence, not precision.

1. **Pairing carries information**: pairing head `h`'s `A` with a *different* head's `B` must widen
   the difference spread substantially. If a scrambled pairing gives the same spread, `A` and `B` are
   not measuring the same thing per head and everything below is void.
2. **The instrument returns non-zero**: `sd(diff)` over the band must exceed `0`, reported with its
   absolute value in margin units, not only as a ratio.
3. **Quiet layers**: the layer with the smallest mean `|mean_h|` must also show among the smallest
   `sd(diff)`, or claim 1 of the retraction is wrong on its own terms.

## What this then licenses — and its registered threshold

With `sigma` known as a function of magnitude, each of the eight published effects gets a
**magnitude-matched** measurability test:

```
measurable_h  <=>  |effect_h|  >  1.96 * sigma(|effect_h|)
```

`1.96` is two-sided `alpha = 0.05` against zero. **This is a test against ZERO, not against the
reference distribution** — the two answer different questions and the output must report both
columns side by side, never a single count.

## Boundary, stated before the numbers

- One model (`qwen2.5-1.5b`), one metric (`signed_margin_drop`), one task, `I_final` only.
- `sigma` is estimated in bins, so it is a smooth function of magnitude fitted on 336 points, not a
  per-head quantity. A per-head `sigma` needs more than two item draws and is **not** claimed here.
- Each arm is a mean over `120` items, so every `sigma` below is the precision **of a 120-item mean**
  and does not transport to a different `n`.
- The `all`-position scope has no second item draw, so nothing here applies to `I_all`.

## What each outcome costs me

**If CONFIRMED:** the retraction stands and is now quantified rather than argued, and `n_measurable`
becomes reportable for the first time.

**If OVER-RETRACTED:** `item_noise_bound()`'s retraction was itself too strong, and a claim this
repository killed has to be partially revived — which would be the second time a self-correction here
overshot, and that pattern would then be the finding rather than the number.

---

# Amendment 1 — the design above was SUPERSEDED before it was written, and by this repository

Appended 2026-07-28, minutes after the section above, **before any statistic was computed.**

## What happened

The Bland–Altman design above is a re-derivation. Commit `6890700` already ran it, better: R11's
runner stores `per_head_sem = sd_over_items/sqrt(n)` **per head**, so the measurement error is a
direct within-run quantity and does not need a two-arm difference at all. That commit reported `8` of
`8` measurable, `0` of `8` distinguishable, and checked the two estimators against each other —
run-to-run disagreement fell inside the SEM band `164` of `168` times, `97.6%` against a nominal
`95.45%`.

**The reason I walked into it is a stale signpost in the handle itself.** `item_noise_bound()`'s
retraction still ends:

> THE DIRECT TEST IS NOW THE ONLY ROUTE, and it is cheap: re-run the same heads on a DISJOINT item
> set and store `sd_over_items/sqrt(n)` per head. The runner already computes the per-item drops and
> throws them away.

That was true when written and false one commit later. **It sits at the exact decision point a reader
arrives at, and it points the wrong way.** A comment is a hypothesis; I believed the sentence instead
of opening the file it describes. The sentence is corrected in place rather than deleted, because a
reader who only sees the corrected version loses the fact that it was ever wrong.

**A second thing the diff exposed, which I had not written down beforehand:** the two arms carry
different `code_version` stamps, `b3aee67d` and `a6126d03`. Any A-minus-B estimate of item noise is
therefore contaminated by whatever changed between them. That confound is fatal to the superseded
design and is absent from the `per_head_sem` route, which is one run's own quantity — a second,
independent reason the replacement is the right instrument.

## The residue that is genuinely open

`item_noise_bound()` killed this claim outright:

> DEAD — "at most `0.66%` of the floor's variance can be item sampling."

It was killed for **method** — extrapolating a quiet layer's spread to the band. It was never
recomputed. With per-head SEM in hand the correct decomposition is direct:

```
var(measured effect over heads)  =  var(true effect over heads)  +  mean(sem^2)
item-sampling share of the floor's variance  =  mean(sem^2) / var(measured effect)
```

This is one of the five components the front page says the reference distribution mixes, and it is
the only one that has never been given a number.

## Registered thresholds, before the computation

| outcome | rule | consequence |
|---|---|---|
| **instrument-dominated** | share `> 0.25` | the band floor is substantially measurement error; "component heterogeneity" as its dominant term is **downgraded** on the front page |
| **heterogeneity-dominated** | share `< 0.05` | the item-sampling axis is negligible **at `n = 120`** and must be labelled with that `n` rather than stated unconditionally |
| **intermediate** | otherwise | reported as a number with its CI and no verdict word |

Separately, whether the withdrawn `0.66%` was accidentally close is reported but **carries no
verdict** — a number reached by an unfit method is not vindicated by landing near the right answer.

`N_BOOT = 10000`, seed `20260728`, bootstrap over the `168` band heads.

## Positive controls

1. `per_head_sem` must be strictly positive on every band head, or the SEM route is as blind as the
   quiet-layer route it replaces.
2. The retraction's own premise — that a quiet head is quiet in *both* terms — becomes a direct test:
   `Spearman(|effect_h|, sem_h)` over `336` heads. The retraction argued this from a **layer-level**
   correlation between mean `|drop|` and **between-head spread**, which is a different quantity. If
   the head-level correlation with the actual error term is near zero, the retraction reached the
   right verdict by the wrong argument, and that is worth knowing.

## Boundary

One model, one metric, `I_final` only, `n = 120` items per arm, band `L14-27`. Every `sem` is the
precision of a `120`-item mean.

---

# Amendment 2 — the outcome

Appended 2026-07-28, after running `measurability()`. Thresholds above unchanged.

## Positive controls

| control | returned |
|---|---|
| per-head `sem` strictly positive on every band head | min `0.0013` — the instrument is not blind |
| the retraction's own premise, at head level | `Spearman(|effect|, sem) = +0.5975` over `336` heads, `+0.4878` on the band, `+0.8259` layer-level |

**The retraction was right, and its argument was the wrong one.** It quoted `+0.962` between a
layer's mean `|drop|` and its **between-head spread** — a different pair of quantities. Against the
actual error term the correlation is `+0.5975`, clearly positive but far weaker, so the premise
survives while the number that supported it does not transfer.

**And the dependence is strongly sublinear**, which is the part neither the claim nor its retraction
saw: from the quietest layer to the loudest, `mean |effect|` rises `0.0080 → 0.2399` while `mean sem`
rises only `0.0051 → 0.0134`. Effect grows about thirty-fold; noise grows under three-fold.

## The number

```
item-sampling share of the band floor's variance   0.0194   95% CI [0.0064, 0.0413]
                                          = 1.9436%   against the withdrawn 0.66%
all 336 heads rather than the band                 0.0188
mean sem 0.0169   band sd 0.2446   base margin 4.4177
```

**Verdict: `HETEROGENEITY-DOMINATED`** by the registered rule — the share and its entire CI sit below
`0.05`. **At `n = 120` items the band floor is roughly `98%` true between-head heterogeneity.**

**The withdrawn `0.66%` is reported, not vindicated.** It was low by a factor of about three and its
own value sits at the very bottom of the corrected CI. A number produced by an unfit method is not
made right by landing near the right answer, and the sublinear scaling above is exactly why the
quiet-layer extrapolation ran low.

## The scope that makes this a claim rather than a slogan

`sem^2` scales as `1/n` and the true between-head variance does not, so:

```
item sampling reaches 25% of the floor only at n = 9.3 items
                       5%                        n = 46.6 items
```

**`D6` — it assumes nothing else about the task changes with `n`.** But it converts *"item sampling
is negligible"* into *"item sampling is negligible above roughly fifty items"*, which is a statement
with a boundary. Every published number here uses `n = 120`.

## What this does and does not settle

**Settles:** one of the five components the front page says the reference distribution mixes now has
a number and a CI, on one model and one metric.

**Does not settle:** the other four. And it says nothing about `I_all`, which has no second item draw
and no stored `sem` — so the `2.0051x` scale difference between the two intervention supports remains
undecomposed.

---

# Amendment 3 — a name collision exposed a wrong tie rule that had shipped for twenty rounds

Appended 2026-07-28. Not part of the registered design; found while running it.

Adding a helper named `_spearman` for Amendment 2's positive control created a **second definition of
a name that already existed** at `headline.py:180`. The later definition wins, and `make verify`
immediately reported a published number had moved:

```
STALE: REF depth vs clearing rate is 0.6493557139430766, the README says 0.645
```

The original rank rule was `rk = lambda v: [sorted(v).index(x) for x in v]` — every member of a tied
group receives the group's **minimum** rank. That is not a convention choice; it is the wrong rank
transform for Spearman, which uses midranks.

**Blast radius, measured rather than asserted.** Eight verdict-bearing functions re-run under both
rules — `r18`, `item_noise_bound`, `depth_sensitivity`, `r15`, `rank_vs_role`, `r1_floor_audit`, `r9`,
`ov_copying` — return **byte-identical output**. They correlate continuous quantities, which do not
tie. Only `spearman_layer_vs_clearing_rate` moved, `+0.645 → +0.6494`, because clearing **counts** are
small integers and tie constantly.

**The lesson is the detection path, not the number.** A wrong tie rule that only bites on tied data,
in a codebase whose Spearmans are mostly over floats, is invisible to every test that passes. It was
caught by an accident — a duplicate name — and not by any check here. The repair is one definition,
midranks, with the old rule recorded in the docstring rather than erased.
