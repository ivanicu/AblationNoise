# R5 — site, readout, or mechanism size?

A 2×2 on one task, one mechanism per model identified in-run, **each cell measuring its own null and
running its own positive control**.

    site     final position only | all positions
    readout  4-way answer margin | full-vocab KL against the unablated distribution

**The claim is the effect-to-floor ratio, because absolute scales differ ~100× across models.**

| model | readout | final | all | change |
|---|---|---|---|---|
| phi-3.5-mini | margin | 0.98 | 0.25 | **0.25×** |
| phi-3.5-mini | kl | 1.67 | 1.18 | 0.70× |
| qwen2.5-1.5b | margin | 0.97 | 0.31 | 0.32× |
| qwen2.5-1.5b | kl | 2.84 | 0.58 | **0.20×** |
| qwen2.5-3b | margin | 1.36 | 0.98 | 0.72× |
| qwen2.5-3b | kl | 0.76 | 0.28 | 0.37× |

**Six of six worse — and under two independent floor definitions.** Readability is `|effect| /
floor`, and the two candidate floors disagree about magnitude while agreeing about direction in
every cell:

```
floor = 2 sd        worse in 6 of 6    floor widens 1.31-3.34x
floor = p10-p90     worse in 6 of 6    floor widens 1.39-5.46x
|effect| itself changes 0.69-1.94x
```

So the direction is a property of the data and the magnitude is a property of the statistic. When an
ablation shows nothing the reflex is to ablate harder; on every model, both readouts and both floor
definitions, that makes the measurement worse.

> **Corrected 2026-07-27.** This paragraph previously read *"the floor widens 2.4–5.2× while the
> effect changes by 0.90–1.94×"*. Neither range reproduces from the checked-in results under any
> floor definition; both were quoted from a commit message rather than computed. `make verify` now
> recomputes and asserts every number above, and fails the build if one drifts. The 6-of-6 verdict
> is unaffected — it was never the number that was wrong.

**Readability is a ratio, not a size.** phi's clearing cell has an effect **100× smaller** than the
1.5B's. A small effect on a small floor is readable; a large effect on a larger floor is not.

**The readout axis is withdrawn.** Each model cleared on a different column — phi on both, the 1.5B
only on KL, the 3B only on margin. And the in-run identification found a much weaker head on the 3B
(final-position attention 0.244 against 0.852 and 0.877), so mechanism strength is unmatched across
models and that axis is **confounded, not null**. Separating it needs a design that matches
mechanism strength, not more models.

**The pre-registered lean was wrong.** [PREREGISTRATION.md](PREREGISTRATION.md) records the author's
expectation that *no* cell would clear, written down specifically so it could not be revised
afterwards. One cell cleared on the first model and four of six across three.

**A consistency check that passed.** The in-run identification rule reproduced the previously
established copy head exactly on the 1.5B, agreeing with an experiment that used a different method.
