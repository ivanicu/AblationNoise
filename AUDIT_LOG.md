# Audit log — gates that failed, and the runs that judged the gates

> Split out of `README.md` on 2026-07-28 without rewriting.

## Two rounds returned `NOT MET`. A separator run on the existing files says the gate was wrong, not the instrument.

R6 and R7 both stopped short of their gates. **The two rounds lost cells for two different
reasons**, and an earlier draft of this section collapsed them into one — corrected here:

| cell | why it was dropped |
|---|---|
| `phi-3.5-mini` (R6, R7) | its `mean` arm's positive control did not clear its own floor → cell declared invalid |
| `internlm2-1.8b` (R7) | its **zero** arm's `ratio_k1` is 0.98 → R1's live-sham exclusion. **Nothing to do with any positive control** |

The separator below addresses only the **first** reason. It cost zero compute — every number was
already in the checked-in results:

```
by displacement ratio   qwen2.5-1.5b 0.141 < qwen2.5-3b 0.148 < phi 0.232 < internlm2 0.272
by mean-arm readability phi 0.64 < qwen2.5-1.5b 1.03 < internlm2 2.06 < qwen2.5-3b 2.38
                                                              -> different orders
```

**The `mean` arm's failure does not track how small its perturbation is.** It tracks how readable
that *model* is at all: the mean arm sits at a stable **0.23–0.44** of the same model's zero arm on
every one of the four, and it crosses the `|PC| > 1 band sd` line only where the model's zero arm is
itself low. That is a threshold crossing a smooth quantity — not an instrument failing.

So the honest restatement, **scoped to the cells it covers**: the cells dropped for a *dead `mean`
arm* were dropped by a threshold crossing a smooth quantity, not by a broken measurement. That is
one of the two reasons. The other — `internlm2`'s band ≈ sham — is untouched by this argument and
remains a real exclusion. R8 already stopped using `mean` as a denominator and moved to a
within-cell ordering; this is evidence that the change was necessary rather than convenient, and it
is **not** evidence that every `NOT MET` was an artifact.

> **What would break this argument, stated because it is missing otherwise.** If a positive control
> can be re-admitted whenever its magnitude is "smoothly continuous" with other models', then no
> positive-control check can ever exclude anything — any failure is re-describable after the fact.
> The criterion that separates the two cases is *whether the failing arm's deficit tracks the
> intervention or the model*, and it is only checkable because four models exist. On three it would
> not have been.

*(The 0.23–0.44 fraction is **not** a matched comparison — `zero` displaces by ‖x‖ and `mean` by
`d`, which R6 measured at 14–27% of it. It says nothing about direction. What it says is that the
fraction is stable, which is the whole point.)*

