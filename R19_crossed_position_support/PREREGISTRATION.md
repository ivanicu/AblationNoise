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

### H-published · the eight are enriched
Requires **all three**: matched-layer set randomization `p < 0.05` · confirmatory effect direction
matching the original claim · holding on **both** `all`-position and position-averaged estimands.

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
