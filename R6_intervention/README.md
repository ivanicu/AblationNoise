# R6 — is the floor a property of ablation, or a property of *zeroing*?

Every number in R1, R2, R4 and R5 came from setting a component's output to **zero**. A head's
output is never zero in normal operation, so zeroing hands the downstream layers an input they never
see. If the floor is that off-distribution damage, this repository's headline shrinks to a
restatement of advice the field already publishes.

[The pre-registration](PREREGISTRATION.md) committed, before any result existed, to **rewriting the
first sentence of the top-level README in the same commit as the result** if that turned out to be
the case.

```bash
python3 R6_intervention/run.py --model <hf-path> --tag <name>          # the three arms
python3 R6_intervention/diag_item_variance.py --model <hf-path> --tag <name>   # the diagnostic
```

---

## Verdict: `NOT MET` — and the reason is worth more than the gate would have been

**The gate was not evaluated.** The pre-registration requires at least three models that are both
*informative* (their zero-arm separates band from sham) and pass both round-invalidating checks.
Exactly **one** qualifies. The pre-registration says what to do in that case, and it is done:

> *if fewer than 3 models complete, R6 reports what it has and the gate returns NOT MET rather than
> ruling on two models.*

## What did happen, in the order it happened

### 1. The zero arm reproduced R1 exactly, on four models out of four

| | R1's checked-in `ratio_k1` | R6's zero arm | apart |
|---|---|---|---|
| qwen2.5-1.5b | 4.31× | 4.31× | **0.0%** |
| qwen2.5-3b | 6.73× | 6.73× | **0.0%** |
| phi-3.5-mini | 12.27× | 12.27× | **0.0%** |
| internlm2-1.8b | 0.98× | 0.98× | **0.0%** |

Through a completely rewritten measurement path — three interventions in one hook, an added capture
pass, a derangement, a different runner. **R1's number is not an artifact of R1's own code**, and
this is now the most solid fact in the repository. It cost nothing: it is what you get for insisting
that a new round's control arm *be* the old round's measurement rather than resemble it.

### 2. The pre-registered statistic turned out to be degenerate

`ratio_k1 = band floor / sham floor`. The sham arm draws from the **early** layers, and there an
on-distribution write is nearly the identity — so its sd collapses by up to **547×** and the ratio
divides by it, reporting values from 113× to 2133×.

Taken at face value the gate would have read `ZERO-IS-THE-ARTIFACT` and the front page would have
been rewritten **on a division by zero**. [AMENDMENT 1](AMENDMENT_1_statistic_degenerates.md),
committed before the second model finished, replaces it with
`readability = |positive control| / band sd` — a known effect against the same arm's own null,
neither term able to vanish.

> **The lesson is one level past R4's.** R4 was withdrawn because its pre-registration named a gate
> and left the estimator open. R6 named the estimator in full — and named one that is only
> well-conditioned for the intervention it was written from. **Naming the estimator is necessary and
> not sufficient: it must also survive the factor under test.** The check is mechanical — for each
> arm of the design, ask which quantity in the statistic can go to zero, and whether that arm can
> drive it there.

### 3. Under the amended statistic, all four models moved the same way — and it is the *opposite* of the pre-registered worry

| model | zero | mean | resample | `rr` mean | `rr` resample | checks |
|---|---|---|---|---|---|---|
| qwen2.5-3b | 10.07 | 2.38 | 1.57 | 0.24 | 0.16 | both pass |
| internlm2-1.8b | 4.69 | 2.06 | 2.09 | 0.44 | 0.45 | both pass, **not informative** |
| phi-3.5-mini | 2.78 | 0.64 | 0.60 | 0.23 | 0.22 | **positive control dead on both arms** |
| qwen2.5-1.5b | 2.35 | 1.03 | 0.77 | 0.44 | 0.33 | **positive control dead on resample** |

A known effect is **harder** to read under on-distribution ablation, not easier — `rr` below 0.67 in
8 of 8 cells. Which is exactly why the next step was not to write that down.

### 4. The strongest confound was not in the pre-registration, and it is the answer

Two worlds explain a small effect, a small floor and a dead positive control, and they are not the
same claim:

* **G — GENTLER.** An on-distribution write really does perturb less *and perturbs the mechanism
  more than random heads*, so signal-to-floor genuinely falls. R6 would then be a real
  dynamic-range result.
* **I — IDENTITY.** A head's output **at the final position** carries little item-specific variance,
  so its mean over items *is* approximately its value on any item. Then mean-ablation is not gentle,
  it is nearly nothing, and every small number above is arithmetic.

The separator needs no ablation at all — just the capture pass the runner already performs:

```
displacement_ratio = || x_i − mean_over_items || / || x_i ||

    world I predicts  << 1        world G predicts  ~ 1
    thresholds written before running:  < 0.2 -> I    > 0.5 -> G    between -> neither
```

| model | median | p10 | p90 | verdict |
|---|---|---|---|---|
| qwen2.5-1.5b | **0.141** | 0.093 | 0.281 | IDENTITY |
| qwen2.5-3b | **0.148** | 0.074 | 0.377 | IDENTITY |
| phi-3.5-mini | 0.232 | 0.105 | 0.513 | neither |
| internlm2-1.8b | 0.272 | 0.205 | 0.351 | neither |

**No model reaches 0.5. World G is refused on all four.** Mean-ablation at the final position
displaces the residual stream by only **14–27%** of what zero-ablation displaces — 4–7× smaller.

## What this means, stated as small as the evidence allows

**R6's design cannot answer R6's question.** Comparing a floor under zero-ablation with a floor
under an intervention that moves the residual stream five times less is a comparison of two
*magnitudes*, not of two *kinds*. Everything in the table in §3 — the smaller effects, the smaller
floors, the dead positive controls — follows from the perturbation being smaller, and none of it
licenses a statement about on- versus off-distribution.

So, explicitly:

* **The off-distribution worry about zeroing is NOT resolved. It is untested.** R1's headline is not
  vindicated by this round; the test did not run to completion. That distinction is the whole point
  of writing the retraction commitment down beforehand — a test that fails to decide must not be
  reported as a test that passed.
* **The first sentence of the top-level README is not rewritten**, because the condition for
  rewriting it — `ZERO-IS-THE-ARTIFACT` — was not established. Nor was its negation.
* **A finding that is real and transfers:** at the final position of this task, a head's output is
  **73–86% item-independent** across the four models. Any intervention defined as "replace with
  the mean over items" is, there, a small perturbation — and a paper that mean-ablates and reports a
  small effect may be reporting a small *perturbation* rather than an absent mechanism. That is
  checkable in one clean forward pass per item, before any ablation is run.

## What R7 has to do differently

**Norm-match the interventions.** The comparison must hold the size of the perturbation fixed and
vary only its direction — e.g. scale the mean-ablation displacement to `||x_i||`, or compare each
intervention at matched displacement norm rather than at matched *description*. Only then does
"on-distribution versus off-distribution" name a difference between the arms rather than a
difference in how hard they hit.

Two smaller changes the round earned:

* the runner should record `displacement_ratio` in the same pass it captures the means, so the
  diagnostic is never a separate script again;
* `informative` and `has a live positive control` are **different properties** and R6 conflated them
  in its inclusion rule. internlm2 fails the first (sham floor ≈ band floor) and passes the second
  comfortably (4.69 sd); phi passes the first and fails the second. The successor selects on both,
  separately, and says which one each excluded cell failed.
