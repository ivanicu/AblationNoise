# R2 — HOW OFTEN DOES ABLATING A KNOWN MECHANISM GO THE WRONG WAY?

Written 2026-07-27, **before any R2 code exists**. Committed before the runner so the gate cannot be
fitted to what comes back. R1's record: `bc3096d` (pre-registration), `83fae5f` / `85211a1`
(amendments), `5c19e69` (completion).

---

## THE OBSERVATION THIS COMES FROM

E132c ablated a set containing **L22H7 — the head E123 proved is the binding copy head** — as its
positive control. The control did not merely fail to fire. It fired **inverted**: ablating the copy
set **raised** the correct-answer margin by 32%, and it was more extreme than **all thirty** draws
of a size-matched null.

A positive control that moves the wrong way is worse than one that does nothing, because its
magnitude reads as calibration. If a reviewer saw only `|effect| = 1.43, null sd = 0.49` they would
call the instrument well-calibrated.

**n = 1.** One head, one task, one model. That is a case study, and this project has already been
burned three times by treating a case study as a property.

## THE QUESTION, AND WHY IT IS WORTH COMPUTE

> When you ablate a component set whose identity was established **independently**, how often does
> the effect have the **wrong sign**, and how often does it **fail to clear its own noise floor**?

Both halves matter and they are different failures:

* **wrong sign** — the instrument is anti-calibrated. Nothing it says about an unknown set is usable.
* **right sign, inside the floor** — the instrument is merely too blunt. R1 already showed this for
  single heads (7 of this project's 8 measured single-head effects sit inside the k=1 null). R2 asks
  whether it also holds when you ablate a *known mechanism* as a SET.

If either is common, then the standard interpretability move — ablate, observe, conclude — is
unsound far more often than the literature reports, and the reason is checkable in advance.

## THE OBJECT: INDUCTION HEADS, BECAUSE THEIR IDENTITY IS MEASURED NOT CITED

Induction heads (Olsson et al. 2022) are the cleanest ground truth available on this hardware, and
critically **their identity is derived per-model from a measurement, not taken from a paper about a
different checkpoint**:

* feed a random token sequence repeated twice, `[A B C ... A B C ...]`
* an induction head at position of the second `B` attends to the first `C` — the token that followed
  the previous occurrence
* the per-head **prefix-matching score** is that attention mass, averaged over positions and seeds

That score is the independent identity. It is computed before any ablation and it does not use the
outcome the ablation will measure — which is exactly the property E132c's copy head had (established
by E123, independently of E132c's margin).

**Outcome metric:** next-token log-probability on the SECOND copy of the repeated sequence. Induction
is what makes that possible, so the expected sign of ablating induction heads is unambiguous:
performance must **drop**.

## ARMS, all in the same run

| arm | what | expected |
|---|---|---|
| `induction_topk` | the k highest prefix-matching heads | **drop** (positive control) |
| `induction_bottomk` | the k lowest, same layer band | ~nothing (specificity) |
| `random_k` × 30 | size-matched random draws | the null distribution, per R1 |
| `copyhead_topk` | the k highest room-token-attention heads on the binding task | **drop** — this is the E132c arm, re-run on a second task |

The last arm is what connects R2 to the observation that caused it: if the copy head inverts on the
binding task but behaves on induction, the inversion is about the TASK; if it inverts on both, it is
about the head.

## PRE-REGISTERED GATE

Unit of analysis: one **(model × known-mechanism) cell**. Four models × two mechanisms = up to 8
cells; a cell is valid only if its own null has dynamic range (R1's flag: sham/random floor ≤ 0.02
of the metric scale) and the metric is measurable on that model.

```
INVERSION-IS-COMMON     wrong sign in >= 2 of >= 4 valid cells
                        -> E132c is not a one-off. An inverted positive control is a real and
                           reportable failure mode of ablation, and R3's retroactive audit is
                           licensed to look for it in published work.

INVERSION-IS-RARE       wrong sign in 0 of >= 4 valid cells
                        -> the E132c inversion is specific to that head on that task. It stays a
                           case study, the artifact says so, and R2's deliverable becomes the
                           SECOND quantity below instead.

AMBIGUOUS               exactly 1 of >= 4 -> report as a single further instance, claim nothing.
```

**Second quantity, reported always and gated never** (because it is a measurement, not a fork):
the fraction of valid cells where the known mechanism's ablation, *with the right sign*, still fails
to clear 2 sd of its own size-matched null. R1 makes this computable for the first time.

## CONTROLS AND NAMED CONFOUNDS, written before the run

* **Metric scale differs per model**, so every effect is reported both raw and divided by the metric's
  own baseline — Amendment 2 applies unchanged.
* **The strongest confound**: ablating a head that aggregates a token *wherever it appears* removes its
  contribution to competitors as well as to the answer. That is the mechanism I proposed for E132c's
  inversion and it predicts inversion is **task-specific**, appearing where competitors share the
  answer's surface form. The `copyhead_topk`-on-induction arm is the control that separates it.
* **Set size is a confound with mechanism size.** k is fixed at 5 across all arms, and the null draws
  5, so no arm is advantaged by count.
* **Induction score and the outcome metric must not share a definition.** The score is attention mass;
  the outcome is next-token log-probability. Neither is computed from the other.

## STOPPING RULE

Four valid cells minimum. If fewer than four models yield a measurable induction score with a live
null, R2 reports the cells it has and the gate is NOT MET — it does not lower its own bar. Budget:
one GPU-hour; if the induction-score pass alone exceeds that, the arm list is cut before the model
list, and the cut is recorded in the result file as `reduced_scope`.

## WHAT WOULD MAKE THIS WHOLE ROUND WRONG

If the prefix-matching score does not identify heads whose ablation hurts induction **on any model**,
then there is no known mechanism here and R2 has no positive control of its own — the same defect it
is investigating, one level up. That is checked first, on one model, before the full run: if the top-k
induction heads do not beat the bottom-k, the round stops and says so.
