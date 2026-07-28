# R7 AMENDMENT 1 — two of the three pre-registered worlds have identical predictions

Written 2026-07-27, **after the first two cells and before the remaining two finished**. It records a
defect in R7's own pre-registration, found by trying to classify a result rather than by the result
itself, and it narrows what the round is allowed to conclude.

---

## The defect

`PREREGISTRATION.md`'s prediction matrix:

| | `rr(shrink)` | `rr(randdir)` |
|---|---|---|
| **D — DIRECTION MATTERS** | ≠ 1 | ≠ 1, and ≈ `rr(shrink)` |
| **M — THE MANIFOLD IS SPECIAL** | ≠ 1 | ≈ `rr(shrink)`, both ≠ 1, and `mean` is the outlier |

**Those are the same row.** Read as predictions they are indistinguishable: both say the two
off-manifold arms behave alike and differ from the on-manifold one. The pre-registration even
claimed the opposite in prose — *"D and M are separated by `randdir`, which is the arm R6 did not
have"* — and that sentence is false. `randdir` separates `{D, M}` from `S`; it does not separate `D`
from `M`.

This violates the round's own standard, stated in the repository's constitution as *same prediction
across worlds → no discriminating power → find a better action*. It was written into the matrix
anyway, because "the manifold is special" and "direction matters" **feel** like different claims when
stated in English and turn out to be one claim when stated as numbers.

## What R7 can and cannot conclude, restated

* **`S — SIZE IS ALL` remains fully testable and is what the gate turns on.** It predicts `rr ≈ 1`
  on both matched arms, and nothing else does. R7's gate is unchanged.
* **`D` and `M` are hereby merged** into a single surviving alternative — *at fixed perturbation
  size, direction changes readability* — with **no claim about why**. R7 must not report which of
  them holds, in either direction, because its design cannot tell.

## The separator that would actually split them, defined here for the successor

The two English sentences differ in **which component of the head's output the intervention
destroys**, and that is measurable:

* `mean` writes `μ`: it removes the **item-varying** component and leaves the item-constant one.
* `shrink` moves toward the origin: it attacks **both** components in proportion.
* `randdir` adds noise: it destroys **neither**, it only adds.

So the missing arm is the complement of `mean` — remove the item-**constant** component and keep the
item-varying one, norm-matched to the same `d`:

```
constant_only    x  <-  x − (d / ‖μ‖) · μ        ‖displacement‖ = d
```

| | prediction |
|---|---|
| **readability is about destroying the item-CONSTANT part** | `constant_only ≈ shrink`, both ≫ `mean` |
| **readability is about being off the data manifold** | `constant_only ≈ mean`, both ≪ `randdir` |

Those rows are different, which is the property the original matrix lacked. This is **R8**, not a
patch to R7: adding an arm now would mean comparing cells measured by two versions of the runner,
and R5 already recorded what that costs.

## What is unchanged

The gate, the statistic, the three round-invalidating checks, the inclusion rule, and the retraction
commitment. The first two cells pass all three checks — matched displacement to **0.00%** spread,
the zero arm reproducing R1 to **0.0%**, and a live positive control on every arm — so the amendment
narrows the round's conclusions without weakening its evidence.
