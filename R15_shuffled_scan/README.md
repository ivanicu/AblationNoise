# R15 — the ranking half-transfers, and the **floor turns out to depend on the task**

[The pre-registration](PREREGISTRATION.md) was committed before the run, with a kill condition:
*if the ranking does not transfer, every head-level statement in this repository is a statement
about one prompt configuration.*

## The pre-registered primary — and it landed in the band that claims nothing

```
Spearman over the 168 band heads, shuffled vs unshuffled

    on |centred drop|   +0.6092     <- the statistic this repository RANKS BY
    on signed drop      +0.7175

thresholds, committed before the run:   >= 0.7 transfers   .   <= 0.3 does not
```

**The kill did not fire and the pass was not earned.** Two statistics straddle the threshold, and
choosing the one that clears it is a narrative. **Both are reported; neither is claimed.**

## The population confound — checked, and cleared by a measurement not an argument

R15 changed **two** things against R10: line order **and** the correctness filter. One contrast over
two treatments cannot be decomposed — **unless the second treatment is a measured no-op.**

> [R14](../R14_position_vs_binding/) measured `A_orig = 1.000` over `120` items: **the filter has
> never rejected a single item on the unshuffled task for this model.** Filter-on and filter-off are
> the same population there.

Verified directly against both result files: same `draw_seed` `20260727`, same `120` items, same `4`
rooms, same sham band `[0,7]`.

## The finding is the **third** reading, which the pre-registration asked for and did not expect

It asked for per-answer-line floors on the grounds that *"if the floor itself is position-dependent,
a single number for the shuffled task is the same mistake one level up."* **It is.**

```
 line   n    margin    acc     floor    floor/margin
    0   12    4.273   1.000   0.4628       0.108     - primacy
    1   13    3.663   1.000   0.4997       0.136     - primacy
    7   20    2.151   1.000   0.4587       0.213     - recency
    6   14    1.338   0.857   0.4242       0.317
    4   16    1.032   0.750   0.4221       0.409
    5   14    0.657   0.571   0.3011       0.458     - the middle
    3   16    0.593   0.625   0.3324       0.561     - the middle
    2   15    0.567   0.600   0.3589       0.633     - the middle

Spearman(per-line baseline margin, per-line floor) = +0.8810   over 8 lines
```

**The floor is a function of task headroom, not of the model and band alone.** This repository has
been quoting `0.4870` as though it were the latter. **It was measured at baseline margin `4.477`.**

### But it is *sublinear*, and that cuts the other way

```
across lines:   margin spans 7.54x      floor spans 1.66x      floor/margin spans 5.84x
shuffled vs unshuffled:   margin 4.477 -> 1.703 (2.63x)   floor 0.4870 -> 0.4023 (1.21x)
```

**The absolute floor is comparatively robust** — which is exactly what a noise floor should be if it
measures head-to-head variability rather than the task's headroom. **But `×floor` is not portable.**
A head at `0.37×` the floor in one task configuration is not the same object as `0.37×` in another,
and this repository ranks its eight published heads in that unit.

`12` heads clear the floor on the shuffled task against `10` on the unshuffled one.

## What R15 does not claim

* **`+0.6092` is not "the ranking transfers" and not "it does not."** The pre-registration's own
  instruction for the middle band is to report and claim neither, and that is what is done.
* **One shuffle seed** (`90210`). A single permutation is one draw; the per-line table is `n=12`–`20`
  per row, so each row's floor carries real uncertainty and no per-line ranking is claimed.
* **Position-dependence of the floor is not a mechanism.** It says the floor tracks margin at
  `+0.88`; it does not say why, and margin and accuracy move together here so they are not separated.
* **The kill was avoided, not disproved.** A `+0.61` on the ranking statistic is consistent with a
  substantial configuration-specific component, and nothing here bounds it.
