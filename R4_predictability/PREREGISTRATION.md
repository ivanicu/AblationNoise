# R4 — CAN YOU KNOW, BEFORE RUNNING, WHETHER YOUR ABLATION WILL BE READABLE?

Written 2026-07-27, before the analysis. Zero new compute: this uses R1's 52 cells and R2's 5.
R1 `5c19e69`, R2 `2caf48e`, R3 `d888af0` (withdrawn).

## THE QUESTION R1 AND R2 CREATED BY DISAGREEING

    R1 (binding, k=1, final position)   7 of 8 measured effects sit INSIDE their floor
    R2 (induction, k=5, all positions)  0 of 4 sit inside

Same operation — zero head outputs, compare to a size-matched random null — opposite conclusions.
So "ablation effects hide in noise" is neither true nor false in general, and the difference must
be a function of something. If it is a function of things you can observe BEFORE paying for the
outcome, an experimenter can be told in advance whether their planned ablation can resolve anything.

## THE TRAP, NAMED BEFORE THE ANALYSIS

`floor = sd(null) / |baseline|`. The baseline is in the DENOMINATOR OF THE TARGET. Regressing floor
on baseline is therefore **circular by construction** and would produce a beautiful fit that says
nothing. This is the failure `1b283bd` retracted, in a new costume.

So the target is the **raw sd of the null**, and the predictors are quantities that are not
components of it: set size k, layer-band width, head count, hidden size, parameter count, and the
arm (studied band vs early-layer sham). Baseline enters only afterwards, when raw sd is converted
to a floor — and that conversion is arithmetic, not a finding.

**detectors/circularity.py is run on whatever comes out, before it is believed.**

## GATE

```
READABILITY-IS-PREDICTABLE   a model fit on all but one MODEL predicts the held-out model's raw
                             sd within a factor of 2, for at least 3 of the leave-one-out folds
                             -> the tool can warn an experimenter in advance, and that is the
                                deliverable rather than the floor table.

READABILITY-IS-NOT-PREDICTABLE   fewer than 2 folds within a factor of 2
                             -> the floor cannot be anticipated from cheap observables and MUST be
                                measured per setup. That is a stronger argument for the instrument
                                than a predictor would be, and it is the result R1's own Amendment 2
                                already leans toward (four English nouns moved a floor 1.7x).

AMBIGUOUS                    exactly 2 folds.
```

Leave-one-MODEL-out, not leave-one-cell-out: cells within a model share its architecture and its
task instance, so a cell-level split would leak and inflate the fit. Stated now, because that is
the same mistake as an unpaired analysis and this project has already made it once (E78).

## WHAT WOULD MAKE THIS WRONG

n = 5 models is small, and one of them (llama) contributes a single k. A fit that succeeds on this
sample is a hypothesis, not a law, and the round's output is capped at "worth testing on more
models" no matter how good the numbers look.
