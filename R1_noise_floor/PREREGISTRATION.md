# R1 — THE ABLATION NOISE-FLOOR ATLAS (pre-registration)

This is the runner's own module docstring, committed before any result existed.

```
R1 — THE ABLATION NOISE-FLOOR ATLAS.

THE QUESTION. Interpretability papers report the effect of ablating a component (a head, a set of
heads, a layer) and read the size of that effect as evidence of localisation. Almost none report
what a RANDOM component set of the same size does. E132d measured that once, for one model at one
set size, and the answer was large: random 5-head ablation moved the correct-answer margin over a
range of 2.48 on a baseline of 4.48 — 55% of the quantity being measured, in either direction.

If that is general, a large fraction of published localisation effects are inside their own noise.
If it is not, this line dies here. R1 is the gate.

THE ESTIMAND, and it is deliberately dimensionless. Margin is in logits, whose scale differs across
models, so the raw spread is not comparable. Every cell reports

    floor = sd(null draws) / |baseline margin|

which is the fraction of the measured quantity that random component choice alone accounts for.
The MEAN of the null is reported too but is NOT the floor: ablating more components damages more on
average, and that trend is expected and uninteresting. What decides whether a reported effect is
readable is the SPREAD at its own set size.

PRE-REGISTERED GATE (written before the run, and this file is committed before results exist):

    FLOOR-IS-LARGE     median floor over cells >= 0.10   -> the thesis lives: a tenth of the
                       measured quantity is unallocated noise, and published effects must be
                       placed against it.
    FLOOR-IS-SMALL     median floor over cells <  0.03   -> published ablation effects are
                       comfortably outside random variation. The line DIES; pivot to the EM
                       object-level results.
    AMBIGUOUS          in between -> needs more models/sites before any claim.

CONTROLS IN THE SAME RUN.
  * size sweep {1,2,5,10,20} — a floor that only exists at one size is a property of that size.
  * a SHAM ablation (zero a component set OUTSIDE the layer band under study) — if the floor is the
    same there, it is a property of perturbing the model at all, not of the studied circuit.
  * baseline re-measurement per item, so drift in the item set cannot masquerade as effect.

WHAT WOULD MAKE THIS WRONG. The obvious confound: zeroing a head output is off-manifold, so a large
spread might be "any off-manifold perturbation is chaotic" rather than "component choice matters".
That is why the sham arm is in the same run. It does not rescue published claims either way — those
claims use this same off-manifold operation — but it changes what the floor is a floor OF, and the
distinction goes in the write-up rather than being discovered by a reviewer.

```
