# R18 — `final`-only is **not** a proxy for a head, and one of the eight is a top-`4` head under the total intervention

[The pre-registration](PREREGISTRATION.md) was committed before the runner existed. Its readings are
applied here unchanged.

## The positive control passes exactly, and it is the corrected one

R18's original control — *"the mean effect must rise under all-position ablation"* — **was withdrawn
before this run landed** ([`D88`](../DEFECT_LEDGER.md)): `I_all` strictly contains `I_final` in what
it *removes*, but the *effect* need not grow, because cancellation and backup paths can shrink or
flip it. The control that replaced it is structural:

```
at the LAST layer, I_all and I_final differ only in positions no later layer can read
    => eta_h = tau_all − tau_final must be ~0 for every head

observed, L27:   max |eta| = 0.00000        between-head sd = 0.24352 (over the band, which contains L27)        PASS
saturation:      0.29% of cells flip the margin sign   (refusal was set at >50%)
```

**Exactly zero, to every digit stored.** That validates the hook: one line changed from R10's runner
and it does what it says.

## `H-support` fails on **all four** pre-registered components

```
                                    observed     required     verdict
1. Spearman(tau_final, tau_all)      +0.6230       >= 0.9       FAIL
2. published-head verdicts agree        6/8          8/8        FAIL
3. layer-centroid shift               0.1717      <= 0.03       FAIL
4. top-10 overlap                      4/10       >= 8/10       FAIL
```

> **`final`-only is not an acceptable proxy for a head's total output effect on this task.** Every
> head-level number in this repository is about `I_final(L,h)` — the final-query head-output knockout
> — and is now labelled that way rather than as *"ablating a head"*.

**R18's own, looser rank rule gives a different reading and both are reported.** It pre-registered
*transfers* at `≥ 0.7` and *does not* at `≤ 0.3`; `+0.6230` lands **in between**, so by that rule the
instruction is to claim neither, and **the kill does not fire.** The stricter `H-support` bar is the
one that fails. Two thresholds, two verdicts, and picking the convenient one is what the
pre-registrations exist to prevent.

## The eight, under both interventions

```
head      final |c|  xfloor  rank      ALL |c|  xfloor  rank
L16H3        0.5147    1.06    10       0.6872    0.70    21
L17H0        0.0856    0.18    77       1.3703    1.40     4     <- invisible, then 4th of 168
L17H7        0.0831    0.17    79       0.0029    0.00   163     <- present, then gone
L17H11       0.0100    0.02   158       0.0582    0.06   125
L18H9        0.0069    0.01   162       0.1572    0.16    73
L19H0        0.0325    0.07   129       0.0562    0.06   126
L19H5        0.0106    0.02   157       0.0182    0.02   150
L22H7        0.1797    0.37    41       0.2068    0.21    61

floor        0.4870                     0.9766                   2.01x larger
clearing        1/8                        1/8                   -- but not the SAME head
```

**`L17H0` is the result.** Under the intervention this repository has used throughout it sits at
`0.18×` the floor, rank `77` — comfortably inside, one of the seven the audit called unremarkable.
Under the total head knockout it is `1.40×` the floor and **the 4th largest effect of `168`.**

**`L17H7` runs the other way**, from `0.17×` to `0.00×` and rank `163`. The eight do not move
together; the intervention re-sorts them.

> ### ⚠ `L17H0` at rank `4` is a **post-selection descriptive tail**, not a finding — corrected the
> ### same day, by the test this repository had never run
>
> ```
> L17H0 under I_all      |centred| 1.3703 = 2.81 sd      one-head exact randomization p = 0.0296
>                                                        Bonferroni over the 8 tested   p = 0.2367
>
> the SET of eight, matched-layer randomization, 50,000 replicates:   p = 0.6817   NOT enriched
> ```
>
> `168` heads were scanned to surface it, the eight were tested without correction, and **the set
> they belong to is not enriched — it is below the matched-layer null median.** The paragraph above
> is kept because the re-sorting it describes is real and is `R18`'s actual result; what is withdrawn
> is calling `L17H0` *"the result"*, which this page did for one step.

> **The `×floor` column is not comparable across the two arms**, because the floor itself doubles
> (`0.4870 → 0.9766`). That is [R15](../R15_shuffled_scan/)'s finding applied here: `×floor` is not
> portable across configurations, and the intervention is part of the configuration. **Read the
> ranks, which need no threshold.**

## The `|eta|` profile is **not** monotone in depth — the retracted argument was wrong, and the data says so

```
mean |eta| by layer

L 0  0.4541      L 9  0.3989      L18  0.4718      L24  0.0321
L 3  0.2188      L12  0.3912      L21  0.1093      L27  0.0000
L 6  0.1707      L15  0.3973
```

Two steps before this run I argued that the instrument's sensitivity is **monotone** in depth and
that the confound therefore *manufactures* `RELATIVE`. Ivan pointed out that a count of *possible*
downstream readers is not a *magnitude* of missed influence, and that cancellation, backup heads and
interaction terms each break the inference. **That retraction was made on the argument alone. This
profile now confirms it empirically:** large at `L0`, collapsing by `L6`, rising again through
`L18`, then falling to exactly zero at `L27`. **Nothing about it is monotone.**

## The centroid moves **earlier**, by `4.635` layers

```
qwen2.5-1.5b centroid of the clearing profile

final-only    17.235       ( 0.6383 of depth )
all-position  12.600       ( 0.4667 of depth )
```

**This is not yet a verdict on `R12`.** The comparison `R12` turns on needs the same shift measured
on `qwen2.5-3b`, which is [`pueue 232`, running now](PREREGISTRATION.md). If the shift is the same
*fraction* in both models the bias is a depth-fraction bias; if the same *number of layers*, it is
absolute. **Until that lands, `R12` stays `UNVERIFIED`**, and the direction of this shift is
suggestive of nothing on its own — `n=1` model.

### `qwen2.5-3b` landed, and the pre-registered rule returns `UNRESOLVED` — by `3%`

```
                 centroid final -> all      shift (layers)     shift (depth fraction)
qwen2.5-1.5b         17.235 -> 12.600           -4.635               -0.1717
qwen2.5-3b           22.833 -> 19.667           -3.167               -0.0905

positive control, 3b:  last-layer max |eta| = 0.000000        saturation 0.13%

A = |Δfrac₁.₅ᵦ − Δfrac₃ᵦ| × 35 = 2.841     "fraction-shaped" if A ≤ B/2
B = |Δlay₁.₅ᵦ  − Δlay₃ᵦ|       = 1.468     "layer-shaped"    if B ≤ A/2 = 1.421
```

**`B = 1.468` misses `A/2 = 1.421` by `0.047`.** The shift is **more** layer-like than fraction-like,
but not by the margin committed before the run — so the verdict is **`UNRESOLVED` and `R12` stays
`UNVERIFIED`**.

> **Had the threshold been chosen after seeing this, it would have been called layer-shaped.** That
> is what a pre-registration is for, and it is being honoured at a `3%` miss rather than renegotiated.

**What is consistent across both models, under `UNRESOLVED`:** the centroid moves **earlier** under
all-position ablation, by `4.6` and `3.2` layers. The direction replicates; the *shape* of the
dependence does not resolve at `n=2` models.

## What R18 does not claim

* **One model, one task, one vocabulary, `n=120` items, `k=1`.** The ranking comparison is over the
  `168` band heads; the centroid is over all `28` layers.
* **It does not decompose *which* earlier positions matter.** All-or-final is a two-point contrast.
  A per-position sweep is what [`R19`](../R19_crossed_position_support/PREREGISTRATION.md) crosses
  with semantic instance, and it is not this run.
* **`L17H0` at rank `4` is a magnitude result, not a role.** A large total-output effect is not
  evidence that the head carries binding: it could be answer-vocabulary promotion, trajectory
  stabilisation, or generic destruction. **Nothing here separates those**, and the counterfactual
  battery that would is a separate experiment.
* **`6/8` agreement is not `2` heads "changing status"** in a way that survives multiple comparison —
  `168` heads were scanned and the thresholds are the historical `2σ` ones, which
  [the front page now says are not a test](../README.md).
