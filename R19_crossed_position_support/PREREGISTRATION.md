# R19 — pre-registration: crossed **position × intervention-support** exhaustive scan

**Committed 2026-07-28, before the dataset builder or the runner were written.** This supersedes the
patch-a-hole cadence of `R16`–`R18`. It is the first **confirmatory** design in this repository;
everything before it is [frozen as exploratory audit](../README.md).

## The object, named properly

Every earlier round measured

```
x[0, -1, h*HD:(h+1)*HD] = 0
```

which is **not** *"ablate attention head h"*. It is the **final-query head-output knockout**

```
I_final(L,h) :   delta_final_h(x) = m(M(x)) − m(M^{I_final(L,h)}(x))
```

where `m` is the room-logit margin. At the **last** layer, where nothing downstream can re-read
other positions, this equals the head's full output effect on the next token. At earlier layers it
does not, because the head's writes at fact positions may be read by later attention. The total-head
intervention is

```
x[0, :, h*HD:(h+1)*HD] = 0                 I_all(L,h)
```

**`delta_all` ≠ `delta_final` in general, and the gap has never been measured here.**

## Why one experiment and not four rounds

This design closes five gaps at once: *(1)* are the eight heads binding-specific or
position-specific · *(2)* is `final`-only an acceptable proxy for `all` · *(3)* does the depth
centroid move · *(4)* does the random reference distribution change with position · *(5)* do the
published heads transfer across configuration.

## Design

**`64` base binding instances.** Each: `8` persons, `8` objects, `4` rooms used twice, **query
person balanced across instances rather than always `Alice`** — the fixed-query degeneracy `R13`
found. The correct room is fixed within an instance.

**Crossed with `8` query-fact positions × `2` nuisance permutations** → `64 × 8 × 2 = 1024` prompts.
Within a base instance, all `16` prompts share binding, query and answer; **only the queried fact's
line index changes systematically**, with the other seven lines under balanced cyclic permutation.
That is what isolates position — a single shuffle seed, as in `R15`, does not.

> **The statistical unit is the base instance, `n = 64`. Not `1024`.** All bootstraps are **cluster**
> bootstraps resampling base instances with replacement, carrying all `8` positions and both arms.
> Treating `1024` prompts as independent is the error this line exists to forbid.

**Two arms, exhaustively over every head:** `final` and `all`. **No `mean`/`shrink`/`randdir` arms** —
the support question is the one being closed, and adding intervention families would confound it.

## Three metrics, reported separately and never merged into one verdict

| | |
|---|---|
| **signed margin effect** | `delta^m = m_base − m_ablated` — keeps the sign, which this repository has already shown matters |
| **room-set KL** | `KL(P_base(room) ‖ P_ablated(room))` over the `4` room candidates — magnitude without sign, insensitive to margin scale |
| **behavioural flip** | `1[argmax_base ≠ argmax_ablated]` — the only metric that is about behaviour rather than logits |

Activation-patching conclusions are known to be sensitive to metric and aggregation choice.
**Collapsing three into one verdict is how the next retraction gets built.**

## Estimands, fixed now

```
tau^s_h      = E_{b,p} delta^s_{h,b,p}                 position-averaged effect, s in {final, all}
pi^s_{h,p}   = E_b delta^s_{h,b,p} − tau^s_h           position interaction
eta_h        = tau^all_h − tau^final_h                 intervention-support gap  (DIFFERENCE, not
                                                       ratio: zeros, sign changes and cancellation
                                                       make a ratio undefined or explosive)
v_h          = (tau_{h,0} .. tau_{h,7})                per-head position profile
```

**Reference distributions are empirical and conditional, never a scalar.** For every head the null
is `Q(h | layer, position, scope, metric)` and significance is an exact randomization percentile

```
p_h = ( 1 + #{ g in Q_h : |tau_g − mu_Q| >= |tau_h − mu_Q| } ) / ( 1 + |Q_h| )
```

**not** `2 × sd`. With excess kurtosis `+7.43` the normal-theory threshold is not a test. Because
`336` heads are scanned, any "top-k" statement is reported as **post-selection descriptive** unless
it carries FDR or a max-`T` randomization.

## The published-set test, which no earlier round ran

The right question is not *"is head h beyond a scalar floor"* but

> **is the pre-specified set of eight more extreme than a random set holding the same layer
> multiset?**

```
T_pub = (1/8) Σ_{h in H_pub} |tau_h − mu_{Q_h}|

for 50,000 replicates:   for each published head, sample one replacement from the SAME layer
p = P(T_random >= T_pub)
```

Reported on `final` and `all`, and on the position-averaged estimand.

## Pre-registered verdicts — **per hypothesis, not one gate**

### H-support · `final`-only is an acceptable proxy for `all`
Requires **all four**: Spearman(`tau^final`, `tau^all`) `≥ 0.9` · published-head verdicts agree `8/8`
· layer-centroid shift `≤ 0.03` normalized depth · top-10 overlap `≥ 8/10`.
**Any one failing ⇒ `final`-only is not a proxy, and every head-level number in this repository is
relabelled `I_final`.**

### H-position · head effects are stable across position
Requires: median head-wise ICC across positions high · the published heads' position interaction
`π` **not** larger than matched controls' · Spearman(line-`0` rank, position-averaged rank) `≥ 0.8`.

> **⚠ AMENDED — see [Amendment 1](#amendment-1--three-unregistered-thresholds-2026-07-28-before-the-run).
> Two of those three had no number.**

### H-published · the eight are enriched
Requires **all three**: matched-layer set randomization `p < 0.05` · confirmatory effect direction
matching the original claim · holding on **both** `all`-position and position-averaged estimands.

> **⚠ AMENDED — *"matching the original claim"* never said which direction, for which head. See
> [Amendment 1](#amendment-1--three-unregistered-thresholds-2026-07-28-before-the-run).**

### H-depth · `RELATIVE` survives
Requires: the `all`-position profile still supports the relative prediction · **≥ 3** same-family
scales · the profile is **not** a thresholded clearing rate. **With two models this hypothesis is
not testable here and will be reported as `UNTESTED`, not as `UNVERIFIED`.**

## Positive controls, both gating

1. **Support monotonicity is NOT assumed.** `I_all` strictly contains `I_final` in what it removes,
   but the *effect* need not grow — cancellation and backup paths can shrink or flip it. **So there
   is no "mean effect must rise" gate here**; that was `R18`'s, and the reasoning behind it
   [has been retracted](../R12_cross_model/README.md). What *is* gated: at the **last layer**,
   `eta_h` must be `≈ 0` for every head, because there `I_all` and `I_final` are the same
   intervention up to positions no later layer reads. **Last-layer `|eta|` above the between-head sd
   ⇒ the hook is wrong ⇒ `REFUSED`.**
2. **Saturation.** Fraction of `(head, item)` cells whose ablated margin flips sign. `> 50%` under
   `all` ⇒ `REFUSED`: a saturated instrument cannot rank.

## What R19 still will not answer

* **Mechanistic role.** Magnitude is not role. The counterfactual battery — same answer/different
  binding, same binding/different answer, same instance/different position, same position/different
  entity — is a separate experiment and is **not** in this one.
* **Additivity.** Singleton effects say nothing about circuits; pairwise synergy `τ_ij − τ_i − τ_j`
  is not measured here.
* **Cross-model depth law.** Two models is `n=2`; `H-depth` is pre-declared `UNTESTED`.
* **One task family.** Still one synthetic binding task. Transfer is the next thing after this.

## Cost

`1024` prompts × `336` heads × `2` arms `= 688,128` item-forwards per model, batched. `R10` did
`40,320` unbatched in `16` minutes. Submitted through `pueue`, `qwen2.5-1.5b` first.

---

## Amendment 1 — three unregistered thresholds, 2026-07-28, **before the run**

**Committed while `R19` was still queued behind `pueue 232` and its smoke test had not run.** An
amendment written after the run it governs is a narrative; this one is dated by the commit that
carries it and by the absence of any file in `results/`.

**What was wrong.** Three of this document's own thresholds were words, not numbers. **A
pre-registration with a vague threshold is not pre-registered on that axis** — it is a place where a
verdict can be inserted afterwards, which is the single thing the file exists to prevent.

| where | what it said | why that is not a threshold |
|---|---|---|
| `H-position` | *"median head-wise ICC across positions **high**"* | no number, so any observed value can be called high |
| `H-position` | *"position interaction `π` **not larger** than matched controls'"* | no test, no statistic, no cutoff |
| `H-published` | *"confirmatory effect direction **matching the original claim**"* | the eight heads' claimed directions were never enumerated anywhere |

### The replacements, fixed now

**1 · ICC.** `median over heads of ICC(1,1) across the 8 positions ≥ 0.50`, where the variance
components are estimated over the `64` base instances. **`0.50` is a conventional
moderate-reliability boundary and is CHOSEN, not derived** — it is stated so the choice is visible,
and the observed median is reported whatever it is.

**2 · Position interaction.** Statistic: `P_h = sqrt( mean_p pi_h,p^2 )`, the RMS position
interaction of head `h`; set statistic `P_pub = mean over the eight`. Null: replace each published
head with a uniform random head **from its own layer**, `50,000` replicates. **`H-position` requires
one-sided `p ≥ 0.05` for "not more position-dependent than matched controls"**, and a `p < 0.05` in
the other tail is reported as *the eight are MORE position-dependent*, which is a finding rather
than a failure.

**3 · Direction, enumerated.** All eight entered from `E132`/`E132b` as **read-head candidates plus
one externally-known copy head** — heads hypothesised to *carry the answer*. **The claimed direction
for every one of the eight is therefore `HURT`: ablation should LOWER the room-logit margin, i.e.
`tau_h > 0` under the sign convention `drop = margin_base − margin_ablated`.** One-sided throughout.
No per-head exceptions; if a head's original claim was directionally different, this document is
wrong and that is recorded rather than adjusted.

### And a fourth thing, added because `D91` made it necessary

**Discovery / confirmation split, fixed by the build seed.** `D91` established that the eight were
selected, evaluated **and** audited on one item set — the maximal winner's curse — and `R19` was
about to repeat the shape of that error for any head **it** nominates.

```
base instances 0..31   DISCOVERY    -- may nominate heads, describe, explore
base instances 32..63  CONFIRMATION -- the only data any R19-nominated head is judged on
```

**The eight published heads are exempt and are judged on all `64`**, because they were specified by a
prior experiment on a disjoint item family; for them `R19` is already confirmatory. **Any head `R19`
itself surfaces is nominated on `0..31` and tested on `32..63`, or it is reported as
post-selection descriptive.** The split is deterministic from `BUILD_SEED = 20260728` and needs no
extra run.
