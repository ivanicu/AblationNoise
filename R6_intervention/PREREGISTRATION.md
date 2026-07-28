# R6 — IS THE FLOOR A PROPERTY OF ABLATION, OR A PROPERTY OF *ZEROING*?

Written 2026-07-27, before `run.py` exists and before any R6 measurement. R1: `bc3096d`…`5c19e69`.
R4's withdrawal: `abe158b`.

---

## THE GAP THIS ROUND EXISTS TO CLOSE

Every number in R1, R2, R4 and R5 was produced by **setting a head's output slice to zero**. That is
one intervention out of at least three the field uses, and it is the one with the most obvious
alternative explanation:

> **Zeroing takes the residual stream off-distribution.** A head's output is never zero in normal
> operation, so removing *any* head — mechanism or not — hands the downstream layers an input they
> were never trained on. If that is what R1 measured, then the large floor is not a fact about
> ablation. It is a fact about zeroing, the remedy is already known and published (mean-ablate,
> resample-ablate, patch), and this project's headline shrinks to a restatement of it.

**This is the strongest confound to the entire repository, and it has never been run.** R1's own
sham arm does not address it: the sham restores the head after ablating it, so it controls for
*that a hook fired*, not for *what the hook wrote*. Both arms zero.

## THE THREE WORLDS

| | claim | what R1's 2.7–12.3× means under it |
|---|---|---|
| **W1 INTRINSIC** | the floor is a property of removing a component at all | the result stands as written; the floor must be measured whatever the intervention |
| **W2 ZEROING ARTIFACT** | the floor is off-distribution damage | the result is scoped to zero-ablation and largely restates existing advice |
| **W3 SCALE-ONLY** | every intervention has a floor, but of a different size | the *procedure* transfers and no floor VALUE is quotable across intervention types — a stronger version of R1's Amendment 2 |

W1 and W3 predict the same **ratio**. They are separated by the **absolute** floor, so both are
reported and the gate below reads both.

## THE THREE INTERVENTIONS, DEFINED BEFORE THEY ARE IMPLEMENTED

All three replace head *h*'s slice of the `o_proj` input at the **final position only** — identical
to R1, so R6's zero arm must reproduce R1's zero numbers or the round is invalid (see the
round-invalidating check).

| | what is written into the slice |
|---|---|
| `zero` | `0` — R1's intervention, unchanged |
| `mean` | that head's slice **averaged over all items in the run**, at the final position. Computed once, before any ablation, in a single clean pass. |
| `resample` | that head's slice **from a different item**, drawn uniformly from the same item set with a fixed seed, excluding the item being scored. The standard interchange intervention. |

`mean` puts the residual stream at a plausible point that carries no item-specific information.
`resample` puts it at a point that is exactly as on-distribution as a real forward pass but carries
the *wrong* item's information. They fail differently, which is why both are run rather than one.

## THE ESTIMATOR, NAMED IN ADVANCE

**This section exists because R4 did not have it.** R4's pre-registration fixed a gate and left the
predictor set as a class; 60 of 324 admissible estimators returned the opposite verdict, and the
round was withdrawn. So R6 names the statistic, the aggregation, and the comparison — completely.

* **statistic** — `ratio_k1 = band_floor(k=1) / sham_floor(k=1)`, computed by the same code path as
  R1's `run.py`: 30 band draws and 30 sham draws at `DRAW_SEED = 20260727`, band = the upper half of
  layers, `floor = sd(draws) / |baseline margin|`.
* **per-model comparison** — `rr(X) = ratio_k1(X) / ratio_k1(zero)` for `X` in `{mean, resample}`.
  A ratio of ratios: the baseline margin cancels twice, so nothing here can be moved by the
  vocabulary sensitivity Amendment 2 measured.
* **aggregation** — the **median** of `rr` over informative models. Not the mean: R2 measured a
  30-draw null in which one draw was 46× the sd of the others, and this project does not average
  over heavy tails.
* **informative** — a model enters the aggregate iff its `zero`-arm `ratio_k1 > 1.5`, the same live
  sham criterion R1 used to exclude internlm2. Applied per model to the **zero arm only**, so the
  inclusion decision cannot be made by the arm under test.
* **absolute comparison** — `af(X) = band_floor(k=1, X) / band_floor(k=1, zero)`, same aggregation.

There are no other free parameters. No feature selection, no model selection, no threshold tuning,
no choice of summary left open.

## PREDICTION MATRIX

| | `median rr` | `median af` |
|---|---|---|
| **W1 INTRINSIC** | ≈ 1 | ≈ 1 |
| **W2 ZEROING ARTIFACT** | ≫ 1 | ≪ 1 |
| **W3 SCALE-ONLY** | ≈ 1 | ≠ 1 |

## PRE-REGISTERED GATE

```
ZERO-IS-THE-ARTIFACT      median rr >= 3.0  AND  rr >= 2.0 on at least 3 of the informative models
                          -> W2. R1's headline is restated as scoped to zero-ablation, the README's
                             first sentence is rewritten, and the repository's recommendation
                             becomes "use mean/resample" rather than "measure your floor".

FLOOR-SURVIVES            median rr in [0.67, 1.5]  AND  rr in [0.5, 2.0] on at least 3 informative
                          models -> W1 or W3. R1 stands. Whether af is ~1 decides which, and is
                          reported either way rather than gated on.

AMBIGUOUS                 anything else -> report the distribution, claim neither, and name what
                          would separate them.
```

**Retraction commitment.** If `ZERO-IS-THE-ARTIFACT` fires, the top-level README's opening claim is
wrong as written and gets rewritten in the same commit as the result — not in a later cleanup, and
not softened to "in some settings". The sentence *"seven of eight published single-head effects sit
inside the noise floor"* becomes *"…inside the noise floor of zero-ablation, which is the wrong
intervention"*, which is a materially smaller claim, and R1's verdict line changes with it.

## THE ROUND-INVALIDATING CHECK, RUN FIRST

1. **The zero arm must reproduce R1.** `ratio_k1(zero)` must land within 10% of the value in the
   checked-in R1 result file for the same model. It is the same computation on the same seed; a
   difference means the new intervention plumbing changed the old path, and every comparison in the
   round is then between two things that are not what they are labelled.
2. **Each intervention must do something.** Ablating **all heads of one layer** must move the margin
   by more than the band floor of that arm. An intervention with no positive control produces a
   small floor for the same reason a dead instrument does, and R2 established that these two must
   be distinguishable before any null is read (P5). A `mean` arm that writes back nearly the true
   value would return a beautiful small floor and mean nothing.

Failing either → R6 reports NOT MET and no verdict. The gate is not evaluated on a broken arm.

## COST AND THE REDUCTION DECLARED IN ADVANCE

Three interventions × (1 baseline + 30 band + 30 sham + 1 positive control) × 4 models, at k=1 only,
on the same 120-item set R1 used. Roughly 3× R1's k=1 arm; no new model downloads.

* **Only k=1 is run.** k=1 is where R1's finding lives and where the intervention question bites; a
  full set-size sweep triples the cost to answer a question R4 already answered within a model.
* If fewer than **3** models complete, R6 reports what it has and the gate returns NOT MET rather
  than ruling on two models. Same clause as R2 and R3, for the same reason.
* `mean` requires one extra clean pass over the item set to collect the per-head means. That pass is
  cached and reported as `mean_source: 'in-run, all items, final position'` in the result file — a
  mean borrowed from a different item set would be a different intervention wearing this one's name.

Every reduction lands in the result file as `reduced_scope`, with the original values beside it.

## WHY THIS ROUND AND NOT ANOTHER

By the repository's own standard, the highest-leverage action is the one whose worst outcome forces
the biggest update — and here the worst outcome **retracts the top-level README's first sentence**.
No other candidate round does that. Adding a fifth model to R1 cannot; extending R5's factorial
cannot; both are closure. This one can end with the project's headline being scoped down to a
restatement of published advice, which is exactly why it has to be run before the repository is put
in front of anyone.
