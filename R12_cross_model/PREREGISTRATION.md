# R12 — is the hump a fact about depth, or a fact about `qwen2.5-1.5b`?

Written and committed **while `qwen2.5-3b`'s exhaustive run was still executing** (task `59`,
started `10:22:21`, GPU at `99%`). It has not produced a file. Nothing below was chosen after
seeing one.

## The claim under test

[R10](../R10_exhaustive/) + the reference-class analysis found that the fraction of a layer's heads
clearing the **sham-band floor** rises with depth (Spearman `+0.645`) but **not monotonically**:

```
qwen2.5-1.5b, 28 layers, sham floor 0.0792

L0–7    0–8%        L11–14   33–42%       L18–22   42–58%
L8–10   8–17%       L15–17   67–83% ←peak L23–27    8–42%

argmax                   L16, L17
rate-weighted centroid   L17.39      depth fraction 0.6440
```

That hump is the basis for the sharpest sentence on the front page — *the copy head's ablation
number carries **depth** information, not **role** information*. **It is one model.**

## The worlds, and why `qwen2.5-3b` separates them

`qwen2.5-3b` has **36** layers, not 28. That is the whole point: at `28` layers a fixed *layer
index* and a fixed *depth fraction* land in the same place, and at `36` they do not.

| world | what the hump is | predicted **rate-weighted centroid layer** |
|---|---|---|
| **RELATIVE** | a fixed fraction of the way through the stack | **`22.54`** — window **> `20.5`** |
| **ABSOLUTE** | a fixed layer index, whatever the depth | **`17.39`** — window **< `19.5`** |
| **MODEL-SPECIFIC** | neither — the profile has no interior peak | see the kill below |

**`19.5 – 20.5` is declared AMBIGUOUS in advance.** The two predictions are `17.39` and `22.54`;
`20.5` is not a third prediction, it is the midpoint, and the window edges sit half a layer either
side of it. A centroid landing between them separates nothing and will be reported as separating
nothing.

> **Both predictions are emitted by `make headline`** (`reference_class.predicted_centroid_*_36L`),
> so these thresholds are machine-checkable rather than editable prose. Generating them caught an
> arithmetic slip in the first draft of this file, which annotated the relative prediction as
> `≈ 20.5` when `0.6440 × 35 = 22.54`. The *windows* were right — they split the two predictions —
> but the number written beside `RELATIVE` was the midpoint wearing the prediction's label.


## Addendum — 2026-07-28, still before the run produced a file

The statistic these thresholds were derived from **was corrected after they were committed**. Every
null in this repository turned out not to be centred at zero, and `clears the sham floor` became
`|drop − sham mean| > 2 · sham sd`. The sham null's mean is `+0.003977`, so the profile barely
moves — but "barely" is not "not at all", and a pre-registration must be shown to survive a
statistic change rather than quietly re-derived under the new one.

```
                     centroid   depth frac   ABSOLUTE(36L)   RELATIVE(36L)   midpoint
uncentred (committed)  17.3878      0.6440          17.39           22.54       19.96
centred (current rule) 17.2347      0.6383          17.23           22.34       19.79
```

**The windows are NOT changed, and that is the conservative choice rather than the convenient one.**
Under the corrected statistic the two predictions are `17.23` and `22.34`; they still sit on
opposite sides of the committed edges (`< 19.5` and `> 20.5`), and the new midpoint `19.79` is still
inside the declared ambiguous band. **The same windows separate the same worlds.** Moving them would
buy nothing and would be indistinguishable, after the fact, from moving the goalposts.

The peak is unchanged: `L16, L17` at `83%` under both rules.

`make headline` now emits both forms (`clearing_centroid_layer` and
`clearing_centroid_layer_UNCENTRED`), and `--check` asserts both, so this addendum cannot drift from
the thing it describes.

## The kill

> **If `qwen2.5-3b`'s clearing-rate profile has no interior peak — monotone to the final layer, or
> flat with `max rate / min nonzero rate < 2` — then "hump" is a single-model artifact** and the
> depth-information sentence must be re-scoped to `qwen2.5-1.5b` alone.

I do not know which of the three fires. `qwen2.5-3b`'s R9 profile had `rho +0.557` against
`qwen2.5-1.5b`'s `+0.732`, which is weaker and consistent with any of them.

## Secondary readings, fixed now

1. **Peak magnitude.** `qwen2.5-1.5b` peaks at `83%`. No prediction is made about the peak *height*
   — it is recorded so the next model has two points rather than one.
2. **Does the null itself transfer?** The comparison uses each model's **own** sham floor, computed
   from its **own** early layers (`L0–L9` for `36` layers, since the runner takes `NL//4`). A
   cross-model claim built on a shared absolute threshold would be measuring the models' scales, not
   their profiles.
3. **The eight published heads do not exist for this model.** Nothing here can extend `0 of 8`.
   R12 tests the *profile*, not the audit.

## What R12 cannot do

* **`n=2` models.** Two points distinguish "same" from "different" and establish no law — the same
  limit stated for R11's two item sets.
* **One task, one vocabulary, `k=1`.** Unchanged.
* **`phi-3.5-mini` is unavailable and that is a measurement, not a gap.** Its readout was refused:
  the tokenizer scores `pine` on the fragment `p` and `frost` on `fro`, so its margin is not about
  the answer. Recorded in `R10_exhaustive/results/*.REFUSED.json`.
* **A confirmed RELATIVE world would still not explain the hump.** Knowing *where* it sits is not
  knowing *why*, and this round is deliberately not asking why.
