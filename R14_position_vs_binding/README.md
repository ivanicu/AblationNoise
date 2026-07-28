# R14 — the model is not copying line 0, and the shape says why the task looked as if it might be

[R13](../R13_task_audit/) established that this repository's task **cannot** distinguish
position-copying from name-binding: the query is always `Alice`, her fact is always line `0`, and
the two strategies agree on every item. R14 makes them disagree by shuffling the fact lines, so the
answer's fact lands at a uniformly random index.

**Readings fixed in [the pre-registration](PREREGISTRATION.md) before the probe ran.**

```
accuracy ORIGINAL   (answer always at line 0)   1.000
accuracy SHUFFLED   (answer at a random line)   0.800      chance = 0.25

verdict: MIXED     BINDING needed ≥ 0.900 · POSITION needed ≤ 0.350
```

## The pre-registered verdict is `MIXED`, and the confound control is the result

The control was designed to separate two shapes. **It returned a third.**

```
accuracy by the answer's line under shuffling

line   0     1     2     3     4     5     6     7
      1.00  1.00  0.60  0.62  0.75  0.57  0.86  1.00
      └──── ends ────┘                    └── ends ──┘

ends   L0,1,6,7   57/59 = 0.966  ±0.046        ends − middle = +0.327 ±0.129   z = +4.96
middle L2–5       39/61 = 0.639  ±0.121
```

* **Position-copying predicted a step** — line `0` perfect, everything else at chance `0.25`.
* **A primacy effect predicted a smooth decay** with distance from the start.
* **What came back is a U** — primacy *and* recency, a serial-position curve, which is neither.

**Every line is above chance.** The worst is line `5` at `0.57` — `2.3×` chance, with a lower 95%
bound of `0.31`. **The model retrieves the right room from any position in the list.**

## What this does to R13's finding, and to two of my own steps

> ### The insinuation was wrong, and it was mine
>
> R13's finding about the **task** stands exactly as written: it is fixed-position, and it cannot
> tell the two strategies apart. But across two steps I let that hang as an implication about the
> **model** — that `L22H7` "may be copying from position `0`". **The model is not copying position
> `0`.** It answers correctly `64%` of the time when the answer sits in the middle of the list and
> `100%` when it sits at either end, against a chance of `25%`.
>
> The pre-registration named this outcome as a kill pointing at my own last two steps and required
> it be reported as loudly as the other one. It fired.

**What survives from R13**: the task *permits* a degenerate strategy, so no measurement taken on it
can *establish* binding. That is a statement about what the evidence can support, and it is
unchanged. **What dies**: the suggestion that the degeneracy is what the model exploits.

**And accuracy does drop** — `1.000` → `0.800`. Position is not irrelevant; it is not the mechanism
either. The honest sentence is the one the pre-registration allows: `MIXED`, with the shape.

## What R14 does not claim

* **`MIXED` is not a compromise reading.** It is the pre-registered label for a result between the
  two thresholds, and the *shape* carries what the label cannot.
* **`n` per line is `12`–`20`.** The middle dip is real at `z = +4.96` pooled, but no individual
  line's value is precise to better than roughly `±0.13`.
* **One model, one task, one vocabulary, no ablation.** R14 measures behaviour, not heads. Whether
  the *head-level* results transfer to the shuffled task needs the exhaustive scan re-run on it, and
  that has not been done.
* **A serial-position curve is a description, not an explanation.** Naming it does not say what
  produces it.
