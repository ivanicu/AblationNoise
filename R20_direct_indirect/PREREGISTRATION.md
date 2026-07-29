<!-- unbacked-ok: 2307.15771 2402.15390 2607.01940 -- arXiv identifiers for the self-repair
 literature, not measurements; same class as the identifiers exempted at the top of README.md
 and in R6_intervention/ALIGNMENT_PREREGISTRATION.md. -->
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

---

# Amendment 1 — the control failed three times, all three failures were mine, and then the registered verdict rule fired the wrong word

Appended 2026-07-29. **No threshold above was changed.** The registered rule was applied as written,
returned `SELF-REPAIR-PRESENT`, and **that word is wrong** — the rule is unfit for its own statistic.
Recorded rather than re-specified.

## The registered positive control was built on a false premise and could never have passed

> *"Layer `27` has nothing downstream."*

**It does.** A decoder block is `h = h + attn(ln1(h))` then `h = h + mlp(ln2(h))`, so layer `L`'s
attention is followed by **layer `L`'s own MLP**. There is no head anywhere in the stack with zero
downstream computation. The control failed at `0.224991` against a limit of `0.012176`, `18x` over.

Three repairs, each made **after** seeing the previous failure — a weaker position than a registered
pass, and labelled as one:

| | max `\|direct - total\|` over the `12` last-layer heads | |
|---|---|---|
| **registered**: no MLP, fixed comparator | `0.224991` | **FAIL** |
| **repair 1+2**: re-run the block's own MLP | `0.324917` | **FAIL, and worse** |
| **repair 3**: + R10's own recomputed comparator | **`0.0000041`** | **PASS** |

**Repair 1 got worse because of a second bug, and it was mine too.** The pre-MLP capture hook lives
on the very layernorm the control re-invokes, so from the second head onward the cache held the
*previous* head's modified residual and each head subtracted from an already-damaged vector. The
per-head errors named it: head `0` exact at `0.0034`, head `1` near, then every later head pinned
around `0.6`. **A capture hook fires again when you re-invoke the module to analyse it.**

**Repair 3 is the fourth confound this file registered before the run, collecting on itself.** The
decomposition holds the clean comparator fixed; R10 recomputes `max over the other three rooms`
after every ablation. `L27H02` has a comparator-flip rate of `0.25`, the highest of the twelve, and
was the single head still failing at `0.3249` while the other eleven sat under `0.031`.

With R10's own convention the decomposition reproduces its measured ablation to **`4.1e-06`** on all
twelve heads. **The direct-path arithmetic is exactly right, and the case where it must be exact now
proves it.**

## The registered verdict rule fired `SELF-REPAIR-PRESENT` on data that says the opposite

Two breaks, both in the registration:

1. **`median(suppression) <= 0.80` was written expecting a ratio in `[0,1]`.** `suppression` is a
   ratio of two **signed** quantities whose denominator crosses zero — Cauchy-like. Observed median
   `-0.1417`, quartiles `[-31.19, -3.09, -0.17, +0.78, +49.47]`. A large **negative** ratio means the
   total has the **opposite sign** to the direct path, which is not suppression at all, and it
   satisfies `<= 0.80` trivially.
2. **The sign test is two-sided and the rule reads only its `p`, never its direction.**
   `|total| < |direct|` holds on `53` of `168` — so the significant direction is
   `|total| > |direct|`, which **this file's own null reasoning says World N predicts**.

> **A claim whose test is not its own statement, committed inside a pre-registration, for the second
> time in this repository** (R10's `POWER_PREREGISTRATION` has the first). The verdict is therefore
> **`UNVERIFIED`** — the check was unfit, which is not an acquittal, and specifically **not evidence
> for self-repair**.

## What the data does say, on statistics that have no zero-crossing denominator

```
|total| > |direct|                     115 of 168      sign-test p 1.95379e-06
sign(total) == sign(direct)             79 of 168      p 0.4876   -- a coin flip
median |total| 0.066291   median |direct| 0.019936     ratio 3.3251x
pooled Spearman(|total|, |direct|)                     +0.0166
within-layer partial(|centred total|, |direct| | mean_norm)  +0.2265  p 0.0078  null 97.5th 0.1655
```

**World R — self-repair — is dead.** A restorative dynamic requires `|total| < |direct|`; the
opposite holds, at `p = 2e-06`.

**World A — systematic amplification — is dead too.** Amplification requires the indirect term to
push the *same way* as the direct one; sign agreement is `47%`, indistinguishable from chance.

**What survives is World N with a term nobody sized.** The rest of the network's response is
**`3.3x` larger in magnitude than the head's own contribution to the readout, and its sign is
uncorrelated with it.** Pooled, the two are unrelated (`+0.0166`). Within layer and controlling
`mean_norm`, `direct` is a **real but small** predictor — `+0.2265`, `p = 0.0078`, clearing its own
depth-preserving null — which makes it the **strongest** single within-layer partial found so far
after magnitude (`+0.3388`), ahead of readout reach (`+0.1712`).

## The sentence this rewrites

`R6_intervention/ALIGNMENT_PREREGISTRATION.md` Amendment 1 says:

> *"What remains is not a property of the head — it is a property of what the rest of the network
> does when the head is gone. **That is compensation.**"*

**The first half survives and is stronger than it claimed** — the rest of the network's response is
not a residual, it is the *majority* of the measured effect. **The second half is refuted.** The
response is not compensation: it does not restore, it does not consistently amplify, and it is
sign-uncorrelated with the damage. The named next experiment — co-ablation for self-repair — is
pointed at a mechanism this measurement does not support.

## Boundary

One model, one metric, one task, `I_final` support, `168` band heads, `n = 120` items, direct path
only. `direct` excludes any influence routed through a later component, so a head whose entire
effect is mediated has `direct ~ 0` by construction — `46` of `168` fall below the registered
`0.01` threshold and are excluded from the ratio, though not from the sign and magnitude counts.
The comparator-flip rate averages `0.0231` and reaches `0.6167` on one head; the decomposition uses
the fixed clean comparator throughout and only the control uses R10's. Nothing here establishes
*which* component produces the indirect term.
