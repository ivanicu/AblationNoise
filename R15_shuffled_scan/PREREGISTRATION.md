# R15 — the head-level scan on the shuffled task, and the design defect caught **before** the run

Written while the GPU is occupied by another session's jobs. **No R15 run exists.**

[R14](../R14_position_vs_binding/) showed the model does not exploit the task's fixed position, but
that its accuracy is **position-dependent** — `1.000` unshuffled, `0.800` shuffled, in a U-shaped
serial-position curve. So every head-level number in this repository is measured in **one cell** of
a configuration space the model demonstrably treats differently: *the answer is always at line `0`*.

R15 is the obvious repair — re-run the exhaustive scan on the shuffled task. **It would have been
run wrong.**

## The defect, quantified from R14's own per-item records

The exhaustive runner keeps only items the model answers **correctly**, stopping at `120`. Under
shuffling `24` of `120` are wrong, and **which** ones is position-dependent.

```
line      offered   kept   offered%   kept%    skew
  0            12     12      10.0%   12.5%   +2.5
  1            13     13      10.8%   13.5%   +2.7
  2            15      9      12.5%    9.4%   −3.1
  3            16     10      13.3%   10.4%   −2.9
  4            16     12      13.3%   12.5%   −0.8
  5            14      8      11.7%    8.3%   −3.3
  6            14     12      11.7%   12.5%   +0.8
  7            20     20      16.7%   20.8%   +4.2

ends L0,1,6,7    offered 49.2%  →  kept 59.4%     +10.2 points
middle L2–5      offered 50.8%  →  kept 40.6%     −10.2 points
```

> **A naive shuffled scan measures a population selected toward the positions the model already
> handles best.** The floor it produced would not be the shuffled task's floor — it would be the
> floor of the easy half of it, and nothing in the output would say so.

## The fix, and why it costs nothing

**Drop the correctness filter.** The `drop` is a change in margin, and a margin is defined whether
or not the argmax is correct; the filter was a convenience, not a requirement.

**And it has never been load-bearing.** R14 measured `A_orig = 1.000` over `120` consecutive seeds:
**the filter has never rejected a single item on the original task for `qwen2.5-1.5b`.** So dropping
it changes nothing about any existing number, and prevents a `10.2`-point selection effect on the
new one.

*The filter's original purpose stands where it applies:* a model that cannot do the task at all
should produce a refusal, not a floor. That is what the separate `MIN_ITEMS` refusal branch is for,
and it is unaffected.

## What R15 will report, fixed now

1. **The exhaustive floor on the shuffled task**, unfiltered, against the unshuffled `0.4870`.
2. **The eight published heads' ranks and `×floor`** on the shuffled task, centred on that task's
   own null.
3. **Per-answer-line floors** — because if the floor itself is position-dependent, a single number
   for "the shuffled task" is the same mistake one level up.

## Thresholds

| | |
|---|---|
| the ranking transfers | Spearman of head ranks, shuffled vs unshuffled, **`≥ 0.7`** |
| the ranking does not | **`≤ 0.3`** |
| in between | report it, claim neither |

`0.7`/`0.3` are chosen before the run. R11 measured Spearman `+0.9778` between two *item sets* of
the same task, so anything near that would mean shuffling changes nothing; anything near `0` would
mean the head-level results are specific to the position-`0` configuration.

> **KILL:** if the ranking does not transfer, then every head-level statement in this repository —
> the `1 of 8`, the ranks, the `9`-of-`168` — is a statement about **one prompt configuration**, and
> must be relabelled as such. That is the outcome I expect least and would find most expensive.

## What R15 cannot do

* **One model, one task, one vocabulary.**
* **A transferring ranking would not restore "binding"** — R13's point about what the task can
  *establish* is unchanged by what the heads do.
* **It is blocked on hardware, not on design.** The GPU is occupied by another session; this file is
  the part that does not need it.
