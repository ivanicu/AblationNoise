# Pre-registration — is the unexplained `0.8484` the network REPAIRING itself, and can it be measured without a single ablation run?

Written 2026-07-29, **before the statistic was computed**, committed alone so git ordering rather
than my word establishes that the thresholds preceded the numbers.

## The claim under attack is this repository's own open research question

`R6_intervention/ALIGNMENT_PREREGISTRATION.md` Amendment 1 ends:

> *"What remains is not a property of the head — it is a property of what the rest of the network
> does when the head is gone. That is compensation, it cannot be read off the weights, and the
> experiment is co-ablation: `2307.15771`, `2402.15390`, `2607.01940`."*

`R6_intervention/RESIDUAL_ARM_PREREGISTRATION.md` Amendment 1 then states plainly that compensation
is **not established** — calling the `I_all` result evidence for it would be *"attributing a
mechanism to a datum that did not require it"*. So the sentence names a mechanism the repository has
never measured, and it has been the named next experiment for a full session.

**And the experiment it names is the wrong one.** Co-ablation asks whether two heads compose. It
does not measure repair.

## The three worlds, and they differ in ontology rather than in a parameter

| | |
|---|---|
| **World R — self-repair** | removing head `h` provokes a *dynamic* response: downstream attention patterns and MLPs at the final position recompute and partially restore the margin. The measured effect is therefore **smaller** than the damage actually done. |
| **World N — no dynamics, only arithmetic** | nothing restores anything. The measured effect is the head's own direct contribution plus whatever the (nonlinear) readout does, with no systematic sign. |
| **World A — amplification** | downstream recomputation makes things **worse**, not better: removing `h` derails later heads that depended on it, so the measured effect **exceeds** the direct damage. |

These are not three values of one parameter. They differ in whether the network has a restorative
dynamic at all, and they imply different research routes: under **R** no static property can ever
explain the residual (which is what three predictors failing already suggests); under **N** the
residual is readout nonlinearity and is in principle static; under **A** the object being measured
is a cascade and single-head attribution is worse than this repository has so far said.

## The cheapest decisive action, and it needs **no ablation runs at all**

`I_final(L,h)` zeroes head `h`'s write **at the final query position** and measures the total margin
drop. That total decomposes exactly:

```
total(h)     = the measured I_final drop                          (already in R10's frozen result)
direct(h)    = the drop from deleting h's write from the FINAL residual, nothing else recomputed
indirect(h)  = total(h) - direct(h)                               the rest of the network's response
```

`direct(h)` is computable from **one clean forward pass per item**: cache each head's `o_proj` input
at the final position, form `a_h = W_O^(h) z_h`, subtract it from the final pre-norm residual, and
re-read the margin. `168` heads, all from the same pass. **The whole experiment is `120` forward
passes**, against the `40,320` R10 spent, and it answers a question co-ablation does not ask.

Two versions of `direct` are computed because the final RMSNorm is **not** linear:

```
direct_linear(h)   remove a_h, keep the CLEAN rms scale      -- pure linear direct path
direct_renorm(h)   remove a_h, RECOMPUTE the rms scale       -- direct path + renormalisation
```

`indirect` is defined against `direct_renorm`, so the normalisation is charged to the direct term
and not smuggled into "what the network did".

## The positive control, and it is exact and free

**Layer `27` has nothing downstream.** A head in the last layer writes into the residual and the
only thing between it and the readout is the final RMSNorm. So for those `12` heads:

```
direct_renorm(27, h)  ==  total(27, h)      to numerical precision
```

**If that fails, the decomposition is wrong and no other row is readable.** Registered as the
`UNVERIFIED` gate: `max |direct_renorm - total|` over the `12` last-layer heads must be
`<= 0.05 x` the band's between-head sd of `total`.

Second control: the clean-run margin must reproduce R10's `base_margin` of `4.476821851730347` on
the same item set, or the items are not the same items.

Third control: `direct_linear` and `direct_renorm` must differ. If they are identical, the
renormalisation term is not being computed and one of the two is a copy.

## The strongest confound, written before the run, and it would have eaten the obvious statistic

**`indirect = total - direct` shares a term with `direct`.** So `corr(direct, indirect)` is
mechanically pushed negative by any noise in `direct`, and a strong negative correlation would be
the *expected* result under **World N** with no repair whatsoever. **That statistic is therefore not
used**, and naming it here is the point: it is the one I would have reached for.

**What is used instead** is the per-head ratio and a sign test, neither of which has the shared-term
artifact:

```
suppression(h) = total(h) / direct_renorm(h)
sign test on   |total(h)| < |direct_renorm(h)|      over the 168 band heads
```

**And the sign test's null is conservative in the direction that matters.** Under **World N**, the
downstream recomputation adds an independent, sign-symmetric perturbation to `direct`; adding
independent noise to a quantity **increases** its expected magnitude. So `World N` predicts
`|total| > |direct|` **more** than half the time, and observing the opposite is evidence *against*
`N` that the null cannot manufacture.

**Fourth confound: the comparator can change identity.** The margin is
`logit[correct] - max over the other three rooms`, and the argmax over the other three may differ
between the clean and the modified residual, making the function piecewise. Both are computed: the
decomposition uses the **clean-run comparator held fixed**, and the **disagreement rate** with the
recomputed argmax is reported. If disagreement is high the fixed-comparator numbers are the ones to
read, and that is stated rather than chosen after the fact.

## Registered thresholds

Population: the `168` band heads `L14`–`L27` of `qwen2.5-1.5b`, R10's own `120` baseline-correct
items, `I_final` support, `signed_margin_drop`.

| verdict | rule |
|---|---|
| **SELF-REPAIR-PRESENT** | `median(suppression) <= 0.80` **and** sign-test `p < 0.05` for `\|total\| < \|direct\|` |
| **AMPLIFICATION** | `median(suppression) >= 1.20` |
| **NO-DYNAMIC-RESPONSE** | `median(suppression)` in `[0.90, 1.10]` and the sign test not significant |
| **MIXED** | anything else |
| **UNVERIFIED** | the layer-`27` control fails |

And reported regardless of the verdict word:

1. **`suppression` by layer**, because a head at `L14` has `13` layers of downstream processing and
   one at `L27` has none. Under **World R** the ratio must depend on depth; under **World N** it
   must not. **That is a second, independent separator inside the same run**, and it does not rely
   on the median clearing any threshold.
2. **whether `direct` explains the residual.** `mechanism()` + `alignment` left `0.8484` of the rank
   ordering unexplained by three *static* predictors. `direct` is the first predictor that is
   activation-based **and** projected onto the readout. Its within-layer partial against
   `|centred total|`, controlling `mean_norm`, is reported with the same depth-preserving
   permutation null, `N_PERM = 20000`, seed `20260729`.

## What each outcome costs me

**`SELF-REPAIR-PRESENT`:** every effect size in this repository is a *net* quantity — damage minus
repair — and the reference distribution's width is partly a distribution of **repair capacity**, not
of importance. That reframes the object the whole repository measures, and it means `I_final` was
never measuring "how much this head contributes".

**`NO-DYNAMIC-RESPONSE`:** the sentence *"what remains is a property of what the rest of the network
does when the head is gone"* is **retracted**. The residual would then be readout nonlinearity plus
item noise, and the co-ablation experiment this repository has been pointing at for a session would
be pointing at nothing. **That is the unwelcome branch and it is why this is worth running.**

**`AMPLIFICATION`:** worse than either — single-head attribution would be measuring a cascade, and
every per-head number here would be an upper bound of unknown tightness.

## Boundary

One model, one metric, one task, `I_final` support only, `168` band heads plus the `12` control
heads at `L27`, `n = 120` items. `direct` is the **direct path only**: a head's write reaching the
readout without being read by any later component. A head whose entire influence is mediated by a
later layer has `direct ~ 0` by construction and its `suppression` ratio is undefined or unstable —
heads with `|direct| < 0.01` in margin units are reported separately rather than folded into the
median. Nothing here is about `I_all`, and nothing here establishes *which* component repairs.
