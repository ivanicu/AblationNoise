<!-- unbacked-ok: 2.4 1.6
 -- THE NEW BAND'S ENDPOINTS, chosen here and not yet measured against anything. They are asserted by
 this amendment, so they carry no backing until `kappa.py` emits the observed ratios; the run that
 follows this file is what makes them checkable. -->
# Amendment 1 — the convergence control demanded accuracy below its own dtype's floor

Registered 2026-07-29, after control 1 failed and the STOP executed, before any rerun. Committed alone.

## What happened

Control 1 as registered: relative error `≤ 1%` at `α = 1/32`, monotone convergence, else stop and read
no `κ`. It failed in `8` of `8` cells and the stop executed — exit `3`, `inferential = False`, no
prediction matrix read.

The emitted per-`α` sequences then answered the question the control existed to ask:

```
L09H00   want +5.656546e-02
  α        1        1/2      1/4      1/8      1/16     1/32
  rel err  3.14e-1  1.51e-1  7.30e-2  3.27e-2  1.16e-2  5.64e-3
L09H03   falls to 3.98e-4 at α = 1/16, then RISES to 2.59e-2 at 1/32
L18H03   falls to 7.39e-3 at α = 1/8,  then RISES to 1.30e-2 at 1/32
```

`L09H00` halves its error five times running as `α` halves — the textbook `O(α)` signature of a correct
first-order derivative. The other two are **U-shaped with an interior minimum**, which is a roundoff
floor: truncation error falls as `α`, roundoff rises as `1/α`, and the minimum sits where they cross.

**A gradient hooked one module later would be wrong by a factor of `W_O` and would show a roughly
constant relative error at every `α`.** That is the discrimination the control was designed to make, and
it made it. The gradient is on the `o_proj` input slice — the tensor R10's ablation zeroes.

So the threshold is the defect, not the instrument. `1%` at the smallest `α` demands accuracy below the
`float32` roundoff floor of the dtype the scans were run in, and no correct implementation could have
passed it.

## The replacement rule

Two conditions, both required, and neither evaluated at the endpoint:

1. **`min` over `α` of the relative error `≤ 1%`.** The best achievable accuracy, wherever in the sweep
   it occurs. A wrong-tensor gradient has no `α` at which it is accurate, so this fails for the world it
   must fail for.
2. **In the truncation-dominated regime, the error must fall by a factor in `[1.6, 2.4]` when `α`
   halves.** Measured over consecutive pairs from `α = 1` down to the pair preceding each cell's own
   minimum. A **two-sided band**: it fails if convergence is slower than first order (a wrong direction,
   or curvature dominating) *and* if it is faster (which would mean the quantity being differenced is
   not what the derivative describes). One-sided "must decrease" would have passed a constant-error
   sequence at `α → 1`, which is why the band is two-sided.

`α = 1/32` stays in the sweep and is still emitted; it is simply no longer the point the rule is read
at. The per-cell `argmin` `α` is emitted too, because *where* the floor sits is a fact about the dtype
and worth having on record.

## Why this can fail in both directions

- Condition 1 is a floor test against `0`, and the current best value across the three inspected cells
  is `3.98e-4` — an order of magnitude inside `1%` — so it is attainable. A `W_O`-wrong gradient would
  miss it at every `α` by roughly the conditioning of `W_O`, which is `5.5` for the block measured in
  R6, so this is not a formality.
- Condition 2's band excludes the observed `L09H00` ratios only if they leave `[1.6, 2.4]`. They are
  `2.08`, `2.07`, `2.23`, `2.81`, `2.06` by inspection of the sequence above — **and `2.81` is outside
  the band**, so this amendment is registering a rule its own motivating example may not satisfy. That
  is deliberate: a band chosen to fit the data it was derived from is not a test. If the rerun fails on
  that pair, the finding is that first-order convergence is not clean even where the derivative is
  right, and `κ` still does not get read.

## What is not being changed

The worlds, the prediction matrix, all four decision thresholds, control 2, the curvature control and
the stopping rule are **untouched**. This amendment moves one convergence criterion and nothing else.
No `κ` has been read, so there is no result for a loosened rule to rescue — which is the only condition
under which loosening a control is legitimate at all.
