# R5 — WHICH FACTOR MADE R1 AND R2 DISAGREE?

Written 2026-07-27 before any R5 code. R1 `5c19e69`, R2 `2caf48e`, R4 `e3ddca4`.

## THE DISAGREEMENT R4 EXPLICITLY DID NOT RESOLVE

    R1  binding task, k=1, FINAL POSITION only, 4-way margin      7 of 8 effects INSIDE the floor
    R2  induction,    k=5, ALL POSITIONS,       full-vocab logprob 0 of 4 INSIDE

Three things differ at once, so the comparison identifies nothing. R5 is a 2x2 on ONE model and ONE
task, changing one factor at a time.

## DESIGN

Object: the binding task on qwen2.5-1.5b — the setting where R1 found effects buried — with the
mechanism whose identity is independently established, L22H7 (the copy head, E123).

    factor A  ablation site   final position only  |  all positions
    factor B  readout         4-way room margin    |  full-vocab KL to the unablated distribution

Four cells. **Each cell measures its own 30-draw random null**, because a larger intervention raises
the effect AND the floor together, and a cell that borrowed another's null would confound the two.
That is the whole point of the design and it is why this costs 4x a single measurement.

## PREDICTIONS, WRITTEN BEFORE RUNNING

* **If READOUT dominates** — a 4-way argmax margin is far coarser than full-vocab KL, so the same
  perturbation moves KL while barely moving the margin — the full-vocab column clears its floor in
  both rows, and R1's "hidden effects" were a readout artifact.
* **If SITE dominates** — all-position ablation is a much larger intervention — the bottom row
  clears. But note it should raise the null too, so the RATIO may not move; a site effect that
  raises effect and floor equally is not a rescue and will be reported as such.
* **If NEITHER** — the difference is mechanism SIZE: one copy head is a small part of the binding
  computation while induction heads are nearly all of induction. No design change rescues it.

**My lean is the third**, and it is on the record so I cannot later claim to have expected a
tidier answer. If the third is right, R5's deliverable is a negative with teeth: you cannot fix an
under-powered ablation by changing where you cut or what you read — only by choosing a mechanism
that is large relative to the metric, or by not making the claim.

## GATE

```
READOUT-EXPLAINS   full-vocab cells clear their own floors while margin cells do not, in BOTH rows
SITE-EXPLAINS      all-position cells clear while final-position cells do not, in BOTH columns
                   (and the effect/floor RATIO must move, not just the effect)
SIZE-EXPLAINS      no cell clears its own floor -> the mechanism is simply too small here
MIXED              any other pattern -> report the 2x2, claim no single factor
```

## CONTROLS

* the same 30 random single heads supply every cell's null, ablated the way that cell ablates
* an all-heads-in-one-layer arm per cell as a positive control, so a cell that resolves NOTHING is
  distinguishable from a cell whose instrument is dead (R2's lesson, applied per cell)
* KL is computed against the unablated distribution on the same prompt, so it needs no answer key
  and cannot inherit the margin's 4-way coarseness
