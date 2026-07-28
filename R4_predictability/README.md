# R4 — can readability be predicted before you pay for the outcome?

R1 and R2 disagreed completely: 7 of 8 effects inside their floor, then 0 of 4. Same operation.
So "ablation effects hide in noise" is neither true nor false in general, and the difference must be
a function of something.

```bash
python3 R4_predictability/run.py          # ~2 seconds, no GPU, no model, no network
```

R4 spends **zero new compute** — it re-analyses the R1 result files checked into this repository.

---

## Verdict, after Amendment 1

| | |
|---|---|
| **within a model** | `FLOOR-IS-A-POWER-LAW-IN-SET-SIZE` — R² **0.935–0.985** |
| **the procedure** | `TWO-MEASURED-POINTS-FIX-THE-CURVE` — 12 held-out cells, median **1.15×**, worst **1.68×**, **12 of 12** within 2× |
| **across models** | **UNVERIFIED** — the pre-registered gate is met or missed depending on a degree of freedom the pre-registration never fixed |

The round originally reported `READABILITY-IS-NOT-PREDICTABLE`, 0 of 5 leave-one-model-out folds.
**That verdict is withdrawn** — see [AMENDMENT_1](AMENDMENT_1_feature_set_unspecified.md). The
pre-registration fixed the *gate* (≥3 of 5 folds within 2×) and the *target* (raw sd, so that the
baseline could not be the denominator of its own predictor), but it specified the predictors only as
a **class**: "quantities that are not components of sd". That class has members.

```
324 admissible feature sets swept (8 predictors, subsets of size 1-4, log and linear target)

folds within 2x   0 -> 112 sets    1 -> 83    2 -> 69    3 -> 45    4 -> 11    5 -> 4
the gate is MET by 60 of 324 (19%)
best set  log k, log n_heads, log baseline  ->  5 of 5 folds within 2x
```

One admissible estimator returns each answer. And the best one fits three model-level parameters to
four model-level observations, so **n = 5 models cannot decide it in either direction** — a 5-of-5
here is no more evidence for predictability than the reported 0-of-5 was against it.

## What survives, and it is the part that matters

Within each model the floor is a clean power law in set size:

| model | exponent | R² | sd at k = 1 / 2 / 5 / 10 / 20 |
|---|---|---|---|
| qwen2.5-1.5b | 0.295 | 0.985 | 0.275 0.343 0.427 0.585 0.648 |
| internlm2-1.8b | 0.436 | 0.960 | 0.031 0.039 0.053 0.071 0.123 |
| phi-3.5-mini | 0.590 | 0.935 | 0.207 0.250 0.532 1.001 0.955 |
| qwen2.5-3b | 0.733 | 0.964 | 0.159 0.268 0.389 1.037 1.330 |

The floor is not noisy — it is highly structured. What does not transfer is *which* power law: the
exponent spans 0.30–0.73 and the measured k=1 sd spans **8.8×** across models on an identical task,
vocabulary and readout.

**So measure two points instead of five.** Fit on k=1 and k=10, predict the rest:

```
held-out cells 12   median factor error 1.15x   worst 1.68x   12 of 12 within 2x
```

This is the deliverable, and note what it does **not** need: no other model, no architecture
feature, no feature selection at all. It is therefore untouched by the amendment that took the
across-model verdict down — the two results were never the same claim.

## The circularity trap was named before the analysis

`floor = sd / |baseline|`, so the baseline is the denominator of the target and regressing floor on
baseline would be circular by construction. The target is therefore the **raw sd** — which is also
why the baseline is admissible as a *predictor*, and why the sweep includes it.

## Scope

n=5 models, one contributing a single set size, one task family. The two-point rule is a hypothesis
worth testing on more models, not a law. The across-model question needs an order of magnitude more
models before a fold error means anything, and no amount of feature engineering on five substitutes
for that.
