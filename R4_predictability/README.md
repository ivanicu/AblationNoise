# R4 — can readability be predicted before you pay for the outcome?

R1 and R2 disagreed completely: 7 of 8 effects inside their floor, then 0 of 4. Same operation.
So "ablation effects hide in noise" is neither true nor false in general, and the difference must be
a function of something.

**Verdict.** `READABILITY-IS-NOT-PREDICTABLE` — leave-one-**model**-out, 0 of 5 folds land within a
factor of 2. Median factor errors: 2.2× · 5.0× · 10.5× · 18.7× · **155.9×**.

**The adversarial check on a negative is "is my model class too weak", and it found the structure.**
Within each model the floor is a clean power law in set size:

| model | exponent | R² | sd at k = 1 / 2 / 5 / 10 / 20 |
|---|---|---|---|
| qwen2.5-1.5b | 0.295 | 0.985 | 0.275 0.343 0.427 0.585 0.648 |
| internlm2-1.8b | 0.436 | 0.960 | 0.031 0.039 0.053 0.071 0.123 |
| phi-3.5-mini | 0.590 | 0.935 | 0.207 0.250 0.532 1.001 0.955 |
| qwen2.5-3b | 0.733 | 0.964 | 0.159 0.268 0.389 1.037 1.330 |

The floor is not noisy — it is highly structured. What does not transfer is *which* power law: the
exponent spans 0.30–0.73 and the k=1 scale spans **8.8×** across models on an identical task.

**So the negative becomes a procedure.** Fit on k=1 and k=10 only, predict the rest:

```
held-out cells 12   median factor error 1.15x   worst 1.68x   12 of 12 within 2x
(the across-model fit's medians on the same data were 2.2x to 155.9x)
```

Two measured points instead of a sweep.

**The circularity trap was named before the analysis.** `floor = sd / |baseline|`, so the baseline is
the denominator of the target and regressing floor on baseline would be circular by construction.
The target is therefore the raw sd.

**Scope.** n=5 models, one contributing a single set size, one task family. The two-point rule is a
hypothesis worth testing on more models, not a law.
