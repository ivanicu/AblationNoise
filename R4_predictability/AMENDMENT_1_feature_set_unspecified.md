# R4 AMENDMENT 1 — the pre-registration fixed the gate and left the feature set free

Written 2026-07-27, **after** R4 reported its verdict and **before** that verdict is restated
anywhere. It downgrades R4's own headline.

## What the pre-registration said

> GATE: leave-one-**MODEL**-out — 3 of 5 folds within a factor of 2 → predictable; fewer than 2 →
> NOT predictable.
>
> The target is therefore the RAW sd, **predictors are quantities that are not components of it**.

The gate is a number. The predictor set is a **class**. Every quantity in `{set size, layers, heads,
baseline margin}` and every monotone transform of them satisfies "not a component of sd", so the
pre-registration licenses a family of models and reports one of them.

## What that costs, measured

`run.py` sweeps the family: 8 predictors, all subsets of size 1–4, target in log and linear space —
**324 fits**, each leave-one-model-out over the same 21 cells.

```
folds within 2x  :  0 -> 112 sets   1 -> 83   2 -> 69   3 -> 45   4 -> 11   5 -> 4
pre-registered gate (>= 3 of 5) is MET by 60 of 324 sets  (19%)
best set  log10(k), log10(n_heads), log10(baseline)  ->  5 of 5 folds within 2x
                                                          (2.0, 1.7, 1.8, 1.4, 1.4)
```

**One admissible choice of predictors returns the opposite verdict.** Nothing in the
pre-registration excludes it, and it was not chosen after seeing the data — it is simply a member
of the licensed family that the reported fit was not.

## Why the sweep is not itself the answer

The best set fits four parameters. Two of its three predictors (`n_heads`, `baseline`) are constant
within a model, so at the level that matters the fit has **four model-level observations and three
model-level parameters**. Five models cannot separate these hypotheses in either direction. A 5-of-5
result here is not evidence of predictability any more than the reported 0-of-5 was evidence
against it.

## The amended verdict

| | before | after |
|---|---|---|
| across models | `READABILITY-IS-NOT-PREDICTABLE`, 0 of 5 folds, median errors 2.2×–155.9× | **UNVERIFIED** — the gate is met or missed depending on a degree of freedom the pre-registration did not fix, and n=5 models cannot decide it |
| within a model | floor is a power law in set size, R² 0.935–0.985 | **unchanged** — reproduced exactly by `run.py` from the checked-in R1 results |
| two-point rule | fit k=1 and k=10, predict the rest: 12/12 within 2×, median 1.15× | **unchanged** — reproduced exactly, and it needs **no feature selection at all** |

The deliverable survives and the negative does not. That is the right way round: the two-point
procedure never depended on the across-model model class, and saying so now stops a
researcher-degrees-of-freedom artifact from being carried as a finding.

## The separate defect this exposed

The original across-model fold errors (2.2 / 5.0 / 10.5 / 18.7 / **155.9**×) are **not reproducible
from this repository**. The analysis was run inline and never saved as a script; no reconstruction
over the 324-set family produces a fold above 15.6×. That is a statement about the reconstruction,
not a refutation of the original — the correct verdict is UNVERIFIED, not OVERTURNED — but a number
that cannot be regenerated must not be quoted as if a reader could check it, so it is removed from
the README rather than repeated with a caveat.

**Standing consequence for later rounds:** a pre-registration that names a gate must also name the
**estimator**, not only the target and the exclusion class. R5's pre-registration already does this
by fixing the 2×2 cells in advance; R1's does by fixing the statistic in Amendment 1. R4 is the
round where the omission was load-bearing.
