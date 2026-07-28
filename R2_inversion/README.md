# R2 — how often does ablating a *known* mechanism go the wrong way?

<!-- unbacked-ok: 32 -- see the note below: this figure is from work not included here -->
**Why it was asked.** A positive control in earlier work fired **inverted**: ablating a set containing
an independently proven copy head *raised* the correct-answer margin by 32%, more extreme than all
thirty draws of its null. **That 32% is the one number on this page a reader cannot check** — it
comes from the private research log this round was cut from, and the run is not included. It is
stated as motivation, not as evidence, and nothing in R2's verdict rests on it. A wrong-signed positive control is worse than a dead one, because its
magnitude reads as calibration. But n=1.

**Verdict.** `INVERSION-IS-RARE` — 0 of 4 valid cells. **The attractive hypothesis died.** Ablating a
mechanism whose identity was established independently moved the outcome in the *expected* direction
on every valid cell, so the earlier inversion is a property of that head on that task, not of
ablation.

| model | baseline P | valid | d_top | null median | IQR | sd | sign |
|---|---|---|---|---|---|---|---|
| qwen2.5-1.5b | 0.811 | yes | −4.728 | −0.0088 | 0.029 | 0.125 | ok |
| qwen2.5-3b | 0.824 | yes | −0.860 | −0.0063 | 0.026 | 0.029 | ok |
| phi-3.5-mini | 0.546 | yes | −1.061 | −0.0080 | 0.028 | **2.491** | ok |
| llama-3.1-8b | 0.636 | yes | −1.224 | −0.0171 | 0.047 | 0.091 | ok |
| internlm2-1.8b | **0.000** | **no** | — | — | — | — | — |

internlm2 assigns probability 5e-6 to the correct next token: it does not do induction at all, so an
ablation effect there is an effect on an absent behaviour. Validity is now enforced in the runner.

**sd is the wrong summary here and the data says so.** phi's null has median −0.008 and IQR 0.028 —
and one draw of thirty at **−13.66**. sd is 2.49 with that draw and 0.054 without, a factor of 46.
Percentiles are reported alongside and are the ones to prefer.

**The mechanism is identified per model, never cited.** A prefix-matching score on doubled random
sequences derives induction heads from *this* checkpoint. Selection uses attention; the outcome uses
next-token log-probability; neither is computed from the other.

[AMENDMENT 1](AMENDMENT_1_specificity.md) — the round-invalidating check **failed as written**,
because it used the lowest-scoring heads as an inert comparator and they are not inert. The fix is
the size-matched random null. The amendment also records a prediction made in it and **refuted
fifteen minutes later**.
