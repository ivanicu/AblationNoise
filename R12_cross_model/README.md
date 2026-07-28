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
