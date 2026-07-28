# R12 — `RELATIVE` fires, with an interval that excludes the rival, and the *shape* does not transfer

[The pre-registration](PREREGISTRATION.md) was committed while `qwen2.5-3b`'s run was still
executing, and its [addendum](PREREGISTRATION.md#addendum--2026-07-28-still-before-the-run-produced-a-file)
re-derived the thresholds under the corrected centring rule **before the run produced a file**.

## The reading

`qwen2.5-3b` has `36` layers against `qwen2.5-1.5b`'s `28`. At `28` a fixed layer *index* and a
fixed depth *fraction* land in the same place; at `36` they are five layers apart. That is what makes
the second model a separator rather than a replication.

```
rate-weighted centroid of the sham-clearing profile

observed          22.833      bootstrap 95% CI  [21.52, 24.01]   (2000 resamples over heads)

ABSOLUTE predicted 17.23      OUTSIDE the interval
RELATIVE predicted 22.34      INSIDE  the interval
window edges       19.5 / 20.5   the CI's lower bound clears 20.5
```

> **`RELATIVE`.** The hump sits at a fixed *fraction* of the way through the stack, not at a fixed
> layer index: `0.6383` of the way through `qwen2.5-1.5b`, `0.6524` through `qwen2.5-3b`.
>
> An interval that **excludes the rival prediction** is a stronger result than a point estimate
> crossing a threshold, and it was not what the pre-registration asked for — it asked only for the
> point.

**The pre-registered kill did not fire.** It required no interior peak — monotone to the final
layer, or `max / min-nonzero rate < 2`. Observed: peak at `L26` of `36`, ratio `9.00`.

## What does **not** transfer — and it is the more useful half

`qwen2.5-1.5b`'s profile is a clean unimodal hump: `0–8%` through the early layers, rising to `83%`
at `L16–L17`, falling back. `qwen2.5-3b`'s is not.

```
L0  12%   L1–L11  all 0%    L12  50%   L13  0%   L14  25% …
L26 56%   L33 50%   L35  0%
```

**Three near-equal local maxima and a dead zone.** With `16` heads per layer a clearing rate carries
a standard error of about `±12` points, so:

```
L26  56% ±24        L12  50% ±24        L33  50% ±24        L19  38% ±24
```

**The peak location is not resolved.** The four highest layers are statistically indistinguishable.
The verdict rests on the **centroid**, which averages over all `36` layers and is well determined;
it does not rest on where the maximum sits, and no claim about a "peak layer" is made for this model.

## ⚠ The verdict is **UNVERIFIED**, because the instrument has a depth bias shaped like the winner

Added after the fact, from the object rather than from a memory of it. Every ablation in this
repository zeroes the final position only — [`R10_exhaustive/run.py:213`](../R10_exhaustive/run.py).
That removes head `h`'s direct write at the final position and everything downstream **of it at that
position**. It does **not** remove `h`'s writes at positions `0..n-2`, which later layers read back
by attention.

```
layers that can read a head's earlier-position writes  =  NL - 1 - L

    L = 0            NL-1 downstream readers      most of the head's influence is UNSEEN
    L = NL-1            0 downstream readers      the measurement is COMPLETE
```

**So the fraction of a head's causal influence this instrument can see is monotone non-decreasing in
`L`.** That is structural — it follows from the shape of a causal decoder, not from any measurement.

**And `(NL−1−L)/NL` is a *fraction of depth*.** An instrument whose blind spot scales with the
fraction of the network remaining downstream will place its centroid at a fixed depth **fraction** in
any model, whatever the truth is. That is the exact shape of `RELATIVE`. **The confound manufactures
`RELATIVE` out of `ABSOLUTE`** — and the two predictions here are `5.6` layers apart with the later
one winning.

### The positive control fires *against* the confound — and does not clear it

A profile produced by the bias alone — flat truth × monotone sensitivity — **must be maximal at the
last layer**.

```
model            NL   centroid   peak L   rate     LAST layer rate
qwen2.5-1.5b     28    17.235      16     0.833         0.167
qwen2.5-3b       36    22.833      26     0.562         0.000   ← global minimum
```

**Both are near minimal exactly where the instrument is complete.** `qwen2.5-3b`'s last layer clears
at `0.000`. So the bias does **not** run the shape, and that is real evidence.

**It does not rescue the centroid.** The centroid is a first moment, and a first moment of
`truth × monotone sensitivity` is pulled late whatever the truth's shape. The control *bounds* the
bias; it does not remove it. It also cannot separate *"sensitivity is nearly flat"* from *"the last
layers genuinely do nothing"* — both produce a low last-layer rate.

> **`RELATIVE` is `UNVERIFIED`, not `OVERTURNED` and not `CONFIRMED`.** The check was unfit for the
> question, which this repository's own rule says is never an acquittal.

**What would settle it**, pre-registered here rather than run: ablate head `h` at **all** positions
and recompute the profile. If the centroid moves earlier in both models by the same *fraction*, the
bias is real and `RELATIVE` was its shadow; if it moves earlier by the same *number of layers*, the
bias is absolute and the depth-fraction reading survives; if it does not move, the bias is
negligible and `RELATIVE` is confirmed. One GPU run, `2 × NL × NH` forward passes.

## What R12 does not claim

* **`n = 2` models.** Two points distinguish *same* from *different* and establish no law — the same
  limit stated for R11's two item sets and R14's one model.
* **A confirmed `RELATIVE` world does not explain the hump.** Knowing *where* it sits is not knowing
  *why*, and this round deliberately does not ask why.
* **`phi-3.5-mini` is refused, not missing.** Its readout scores `pine` on the fragment `p` and
  `frost` on `fro`, so its margin is not about the answer; the refusal is recorded in
  [`R10_exhaustive/results/`](../R10_exhaustive/results/) and is a fact about the model/task pairing.
* **The profile is a description of the *task's* clearing rates**, and [R13](../R13_task_audit/)
  established what that task is: fixed-position retrieval. [R14](../R14_position_vs_binding/) then
  showed the model does not exploit the fixed position — but every number here is still measured on
  the unshuffled task.
