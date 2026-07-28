# R7 — at a fixed perturbation size, does the *direction* change readability?

R1's headline has exactly one serious objection: **zeroing is off-manifold, so of course everything
moves.** [R6](../R6_intervention/) tried to answer it and could not — its own diagnostic showed the
comparison arms displaced the residual stream 4–7× less than zeroing, so it compared magnitudes and
not kinds.

R7 removes that degree of freedom by construction. For item *i* and head *h*, let `d = ‖x − μ‖` be
the distance mean-ablation actually moves. **Three arms write a point exactly `d` away from `x` and
differ only in which way.**

| arm | writes | direction | ‖displacement‖ |
|---|---|---|---|
| `mean` | `μ` | toward the item-average — **on-distribution** | `d` |
| `shrink` | `x·(1 − d/‖x‖)` | toward the origin — **the zeroing direction** | `d` |
| `randdir` | `x + d·u` | unrelated to the data — **off-distribution** | `d` |
| `zero` | `0` | the unmatched **anchor**; must reproduce R1 | `‖x‖` |

---

## Verdict: `NOT MET` on the gate — and one result that does not need the gate

**The gate is not evaluated.** It requires three models that are both *included* (their zero arm
separates band from sham, and its positive control clears its own floor) and *valid* (all three
round-invalidating checks pass). Exactly **two** are. `phi-3.5-mini` is included but invalid — its
`mean` arm's positive control does not clear its own band sd, so every ratio with `mean` in the
denominator is unreliable there. `internlm2-1.8b` is valid but not included — its zero-arm
`ratio_k1` is 0.98, the same live-sham exclusion R1 applied.

**Two of two rounds have now ended `NOT MET` on a count.** That is worth saying plainly rather than
burying: the inclusion-plus-validity conjunction is the binding constraint on this instrument, and
`mean` keeps being the arm that dies. That is not bad luck — R6 measured why. See *What R8 has to do
differently*.

### The three checks all passed on every cell

| | |
|---|---|
| **CHECK 1 — the matching is real** | the three matched arms' realized ‖displacement‖ agree to **0.00%** on all four models. The anchor is 4.7–6.1× the matched step |
| **CHECK 2 — the anchor reproduces R1** | `4.31 / 6.73 / 12.27 / 0.98` — **0.0% apart on 4 of 4**, the second time this has held through a rewritten measurement path |
| **CHECK 3 — every arm has a live positive control** | passes on 3 of 4; `phi`'s `mean` arm is dead, which is what invalidates that cell |

### The result

```
model              zero   mean  shrink  randdir     order                overshoot
internlm2-1.8b     4.69   2.06    3.77     2.80     mean<randdir<shrink   19 (0.57%)
phi-3.5-mini       2.78   0.64    5.68     3.96     mean<randdir<shrink   83 (2.31%)
qwen2.5-1.5b       2.35   1.03    6.92     2.18     mean<randdir<shrink    0
qwen2.5-3b        10.07   2.38    7.43     5.68     mean<randdir<shrink    0

readability = |positive control| / band sd, per arm
```

> ### RETRACTED 2026-07-28 — `randdir` is withdrawn, and with it two thirds of the ordering
>
> This section read **`mean < randdir < shrink` in 4 of 4 cells**. An outside reader pointed at a
> defect the repository had built a detector for and never called: the runners' control check is
> `|PC| > band sd` — **magnitude only**. Checking the sign against the `zero` arm's:
>
> ```
>              zero      mean     shrink    randdir
> internlm2   +0.147   +0.0083   +0.0285   -0.0029  INVERTED
> phi         +0.575   +0.0689   +0.4217   -0.0123  INVERTED
> qwen1.5b    +0.646   +0.0981   +0.1866   -0.0096  INVERTED
> qwen3b      +1.605   -0.0305   +0.1577   -0.0188  INVERTED
>                        INVERTED
> ```
>
> **`randdir`'s positive control is inverted on 4 of 4 models**, and `mean`'s on `qwen2.5-3b`. Its
> "readability" was `|PC| / sd` of a control pointing the wrong way — which is the exact failure
> [R2](../R2_inversion/) was built to hunt: *a wrong-signed positive control is worse than a dead
> one, because its magnitude reads as calibration.* R7 then put that number in the middle of its
> headline ordering.
>
> **What survives**, counting only cells where **both** compared arms' controls point the same way
> as `zero`:
>
> ```
> mean < shrink      3 of 3 admissible cells   (internlm2, phi, qwen2.5-1.5b)
> mean < randdir     0 of 0 admissible cells
> randdir < shrink   0 of 0 admissible cells
> ```

**`mean < shrink` in 3 of 3 admissible cells.** A **within-cell** comparison — two readabilities on
the same model, the same items, the same 30 draws — so it needs no ratio, no cross-model
aggregation and no inclusion rule. It is a weaker claim than the one this page shipped, over fewer
cells, and it is the one the controls support.

> Reported as a secondary statistic and labelled as one. The order was added to the analysis after
> the first two cells and before the last two — the commit is in the history — so it is not a
> pre-registered endpoint and is not what the gate turns on. It is stated because it is the part of
> R7 that does not depend on the machinery the gate could not satisfy.

## What this does to the objection R7 was built to test

The objection says: *zeroing is off-manifold, so of course everything moves, so R1's large floor is
an artifact.* Read as a prediction about signal-to-floor, it says the zeroing direction should be
the **least** readable of the three.

**It is the more readable of the two admissible arms, on 3 of 3 cells whose controls are correctly
signed. The on-manifold direction is the less readable.**

So the objection is not supported here. Reported at the strength the controls allow: an **ordering
over two arms on three cells**, not a gate result, not a four-model claim, and not yet a claim that
R1's floor is vindicated.

## The observation `randdir` leaves behind, held as an observation

Adding a random vector of the *same* norm as the item deviation to **every head of one layer**
**raises** the correct-answer margin — on **4 of 4** models, by 0.003–0.019 margin units, each
outside its own single-head null. R2 went looking for exactly this shape under zero-ablation and
found **0 of 4**. Under a norm-matched random write it is **4 of 4**.

Nothing in R7's pre-registration mentions inversion, so this cannot be a verdict of R7's. It is
recorded here, with its numbers, as the observation that a round designed for something else
happened to make — and as the reason `randdir` cannot serve as a comparison arm until it is
understood.

**What R7 does not say.** [AMENDMENT 1](AMENDMENT_1_two_worlds_had_one_row.md) found that two of the
three pre-registered worlds had **identical rows** in the prediction matrix — *"direction matters"*
and *"the manifold is special"* are one claim in numbers and two in English. R7 therefore reports
the ordering and makes **no claim about why** `mean` sits at the bottom. The arm that would separate
them is defined in the amendment and belongs to R8.

## The guard that fired

`shrink` moves toward the origin by exactly `d`. If `d > ‖x‖` the step passes **through** the origin
and out the other side — the displacement norm is still exactly `d`, **CHECK 1 still passes**, and
the arm is *mislabelled* rather than broken. That is the quiet failure, so the runner counts it
instead of clipping it.

It fired: **102 head-writes**, 2.31% on `phi` and 0.57% on `internlm2`, zero on both Qwens. For
those writes the head's output was closer to the origin than to its own mean across items. Small,
real, and invisible without the counter — the round's ordering result holds on the two models where
the count is exactly zero, which is how it should be checked.

## What R8 has to do differently

1. **Do not put `mean` in a denominator.** It is the smallest perturbation available (R6: 14–27% of
   zeroing) and its positive control has now died on 2 of 8 model-arms across two rounds. Report
   readability per arm and compare within cells; use the ordering, or a reference arm that cannot
   collapse.
2. **Add the arm that splits the merged worlds** — `constant_only`, defined in AMENDMENT 1: remove
   the item-**constant** component and keep the item-varying one, norm-matched to the same `d`. Its
   row differs from both; the original two did not.
3. **Reach three valid cells.** Two rounds have failed on the count. Either widen the model set or
   choose arms whose positive controls do not die — and decide which *before* the run, since
   "loosen the inclusion rule" after seeing two `NOT MET`s is the move this repository exists to
   refuse.
