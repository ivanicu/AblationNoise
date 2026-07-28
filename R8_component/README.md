# R8 — is it the *direction relative to the data*, or *which component* gets destroyed?

[R7](../R7_norm_matched/) matched the perturbation size to 0.00% and found `mean` far less readable
than `shrink`. What it could not say is **why**, because two of its three pre-registered worlds had
identical rows. R8 adds the arm that was supposed to separate them.

R6 measured that a head's final-position output splits cleanly, because it is **73–86%
item-independent**:

```
x  =  μ              +   (x − μ)
      item-CONSTANT       item-VARYING            ‖x − μ‖ / ‖x‖ = 0.14 – 0.27
```

| arm | what it destroys | ‖displacement‖ |
|---|---|---|
| `mean` | the item-**varying** part | `d` |
| **`constant_only`** | the item-**constant** part — `x − (d/‖μ‖)·μ` | `d` |
| `shrink` | **both**, in proportion | `d` |
| `randdir` | **neither** — it only adds | `d` |
| `zero` | everything — the unmatched anchor | `‖x‖` |

---

## Verdict: `NOT MET` — **and this round's prediction matrix was wrong when I wrote it**

**Third round in a row to end `NOT MET` on a count.** One cell of four is order-eligible
(`qwen2.5-1.5b`); the other three fail on a non-zero overshoot count or on R1's live-sham rule.

But the gate is not the main thing that failed here.

### The matrix had a mis-derived row, and correcting it collapses all three worlds

The pre-registration's rows, and what they should have been:

| | `constant_only` vs `mean` | vs `shrink` | vs `randdir` |
|---|---|---|---|
| **C** destroying the item-CONSTANT part matters | ≫ | ≈ | > |
| **F** being off the data manifold matters | ~~≈~~ → **≫** | ~~≪~~ → **≈** | ≈ |
| **V** destroying *any* structured part matters | ≫ | ≈ | ≫ |

**The `F` row was derived from the world's name, not from what the arms physically do.** `mean`
writes `μ` — a real average of real activations, **on** the manifold. `constant_only` writes
`x − (d/‖μ‖)μ` — **off** it. Under `F` those two must differ, not match. I wrote them as matching
because "on-distribution" was the label I had attached to `mean` in R7, and I carried the label
instead of re-deriving the row.

Corrected, **C and F predict the same thing on every admissible arm.** They differ only in the
`randdir` column — and `randdir` is inadmissible (below).

> This is [R7 Amendment 1](../R7_norm_matched/AMENDMENT_1_two_worlds_had_one_row.md)'s failure
> **one level worse**, in the round written to fix it. There the two rows were identical because
> two English sentences meant one thing. Here a row was *wrong*, and the check that would have
> caught it — compare the rows as tuples — was performed, on rows I had derived carelessly.
> **Checking the matrix does not help if the matrix is built from the worlds' names.** Derive each
> row from the arms' physical description, then compare.

### `randdir` is inadmissible here too

Its positive control is **sign-inverted on 3 of 3** R8 cells, exactly as in R7's 4 of 4. `mean`'s is
inverted on `qwen2.5-3b`. So every comparison involving `randdir` has zero admissible cells, and the
one column that separated `C` from `F` is unavailable.

```
                   zero        mean   constant_only      shrink     randdir
phi-3.5-mini    +0.5752     +0.0689       +0.5019      +0.4217    -0.0123  INVERTED
qwen2.5-1.5b    +0.6458     +0.0981       +0.1618      +0.1866    -0.0096  INVERTED
qwen2.5-3b      +1.6054     -0.0305 INV   +0.1714      +0.1577    -0.0188  INVERTED
internlm2-1.8b  +0.1470     +0.0083       +0.0268      +0.0285    -0.0029  INVERTED
```

## What survives, using only correctly-signed arms

| model | `mean` | `constant_only` | `shrink` | admissible |
|---|---|---|---|---|
| internlm2-1.8b | 2.06 | 3.42 | 3.77 | all three |
| phi-3.5-mini | 0.64 | 5.76 | 5.68 | all three |
| qwen2.5-1.5b | 1.03 | 5.06 | 6.92 | all three |
| qwen2.5-3b | *2.38 inverted* | 8.01 | 7.43 | two |

```
constant_only ≈ shrink    4 of 4 cells   ratios 0.91  1.01  0.73  1.08
mean is the lowest        3 of 3 cells where its own control is correctly signed
constant_only ≥ 2 × mean  2 of 3         ratios 1.7  9.0  4.9
```

**Destroying the item-constant component is worth as much as destroying both**, and destroying only
the item-varying component is worth far less — even though `constant_only` removes only 14–27% of
`μ` while `mean` removes the deviation entirely — by construction, it writes `μ` itself.

### One world does die

**`V` is refused.** It predicts that destroying *any* structured part makes an effect readable, so
`mean` — which destroys the item-varying component, a structured part — should be **high**. It is
the **lowest** on 3 of 3 admissible cells.

`C` and `F` both survive and **R8 cannot separate them.** Stated rather than resolved: the arm that
would have done it does not have a usable control.

## The overshoot guard, now on two arms

`shrink` overshoots when `d > ‖x‖`; `constant_only` when `d > ‖μ‖`. Both then pass *through* the
origin — displacement norm still exactly `d`, **CHECK 1 still passes**, arm silently mislabelled.

```
qwen2.5-1.5b     0     phi-3.5-mini   134  (83 shrink + 51 constant_only)
qwen2.5-3b      41  (all constant_only)      internlm2-1.8b   24
```

R8 promoted this from *reported beside the claim* (R7) to *excludes the cell from the order claim*,
which is why only one cell is order-eligible. That is the rule doing its job, not a surprise.

## What R9 has to do

**`randdir` must be repaired or dropped before any round leans on it.** Two rounds have now put an
arm with a systematically inverted control into a headline. `detectors/control_fitness.py` exists
for this and, until 2026-07-28, was **never called by any runner** — the sign check is now in
`make headline`, but it belongs in the runner, before the result file is written.

And the inversion is a finding waiting for its own round: adding a random vector of the item
deviation's norm to every head of one layer **raises** the correct-answer margin, on **4 of 4**
models, each outside its own single-head null.

> **Corrected 2026-07-28.** `internlm2`'s `constant_only` positive control read **+0.0148** in the
> table above; the measured value is **+0.0268**. The other four cells of that row were exact, so
> this was a single mistyped digit, not a copied row — and it sat inside a code fence, where
> Detector 6's fence exemption made it **invisible to `make verify`** for as long as it existed.
> The exemption is now gone: 184 of 476 README numbers had been living behind it, including 54% of
> the front page. Removing it raised the checked count from 16 to 47 in this file alone and
> surfaced exactly this one error. Nothing in the round's conclusions depends on it — the arm's
> sign, which is what that table exists to show, is unchanged.

