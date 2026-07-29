# Amendment 2 — a giant plant is the wrong ruler for a small effect

Registered 2026-07-29, after the boundary run, before the calibration. Commit this file alone.

## The gap

Sharpness separates a planted step (`10.054`) from planted noise (`1.790`, `1.709`) by `5.62x`, so
the statistic works. The ten real `qwen2.5-1.5b` tests score `2.351` to `4.160`, median `3.271` —
between the two, near neither.

**The plant jumps concentration from `0.15` to `0.65`.** Nothing in the data is remotely that large:
the fitted `t` at the observed split is `1.86` to `2.39`. So `10.054` is the sharpness of an
enormous discontinuity, and placing `3.271` against it answers a question nobody asked. A weak real
step and a smooth ramp could both score `3`.

## The three worlds

**A — a real boundary.** The observed sharpness lies in the distribution produced by a *step of the
observed magnitude*, and outside the one produced by a ramp of the observed magnitude.

**C — a broad plateau / smooth rise.** The mirror image.

**D — the question is not answerable at this effect size and this `n`.** The two plant distributions
overlap so heavily that no observed value could have told them apart. **This is a real result, not a
failure**: it says a `28`-layer depth profile carrying a `t` of about `2` contains too little
information to distinguish a boundary from a gradient — by anyone, not just by me.

D is the world I expect and the reason this is worth running: it is the outcome that retires the
question rather than answering it.

## Design

Work directly in the space the test consumes — one concentration value per layer.

1. Take each observed `1.5b` profile. Record its residual scatter `s` after removing the fitted
   two-block means, and the fitted jump `d`.
2. **Step plant**: flat, then `+d` at the observed split, plus Gaussian noise of sd `s`.
3. **Ramp plant**: a linear rise of the same total amplitude `d` across all layers, plus the same
   noise. Same start, same end, same `n` — only the path differs.
4. `400` replicates each. Sharpness on the `min_side=4` curve, as fixed in the previous commit.

Matching the plant to the observed effect size uses the data twice. That is correct here and stated
plainly: this is a **power** question — *at the size actually present, are these worlds separable?* —
not an inference about whether the effect exists.

## Registered thresholds, committed before the run

Let `Gs`, `Gr` be the step and ramp sharpness distributions, `x` the observed median `3.271`.

- **STEP-LIKE** — `x` above the `90th` percentile of `Gr` **and** inside the central `80%` of `Gs`.
- **RAMP-LIKE** — `x` below the `10th` percentile of `Gs` **and** inside the central `80%` of `Gr`.
- **UNDERPOWERED** — the central `80%` intervals of `Gs` and `Gr` overlap by more than `50%` of the
  width of their union. Declared **before** looking at where `x` falls, so it cannot be reached for
  after an inconvenient result.
- **UNVERIFIED** — anything else.

UNDERPOWERED is checked first and wins outright. If the instrument cannot separate the worlds, where
`x` happens to fall is not evidence about them.

## Positive control, required

At the original giant amplitude (`d = 0.5`) the two distributions **must** separate under the same
UNDERPOWERED rule. If they do not, the whole comparison is void and no verdict is read.

## The confound

A ramp and a step with the same endpoints differ in total variance, which changes `t` and therefore
sharpness through a route that has nothing to do with localisation. So the ramp is matched on
**amplitude**, and the run also emits the version matched on **fitted `t`** instead. If the two
matchings disagree, the result is UNVERIFIED and the disagreement is the finding.
