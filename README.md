<!-- unbacked-ok: 2.62 24 41.3 41.26 38 16 3.11 3.14 27.58 17.2 35 -- the fresh-clone verification's wall
 time and peak memory, at two dates. 2.62 s / 24 MB was measured 2026-07-28 before the
 randomization tests existed; 41.26 s / 38 MB is the same handle after them, a 16x growth
 (D106). A runtime cannot be emitted by the thing being timed without circularity, so these
 are dated measurements rather than regenerable values. Also: the detector's own
 false-pass rate, plus the earlier rate and the ceiling.
 2605.24059 2606.05378 2605.29126 2605.00333 2607.01002 2604.01094
 2603.11793 2606.09607 2607.04167 2607.18921 -- arXiv identifiers, not measurements: they name the
 papers that refuted this project's novelty premise and no generator here could emit them.
 57.5 18.1 80.5 1.4 -- results QUOTED FROM 2606.05378 section 6, which this repository did not run.
 29.0 -- 9/31, arithmetic on two counts already shown in the same sentence.
 52.0 3.8 5.2 -- the RETRACTED held-out numbers, kept verbatim so the retraction below can be read
 against what it retracts. They are unbacked BECAUSE they are unreproducible; that is the finding. -->
# AblationNoise

**An ablation effect is reported as a number, and whether that number is large depends entirely on
what a *random* component of the same size does. This repository measures that — and then points
the measurement at its own author's prior work.**

> **⚠ *"its own author's prior work"* is `7` attention-selected read-head **candidates**, published
> under the source experiment's own verdict `W-READ-REDUNDANT`, plus `1` externally-established copy
> head (`L22H7`, from `E123`). **For the seven there was no positive claim to deflate** — the source
> already concluded they are individually redundant, and its own largest reported drop is `10.4%` of
> the base margin. What is new here is not the null but the **instrument**: `E132b` measured no
> reference distribution, ran no matched-layer randomization, tested no all-position intervention and
> used no disjoint item set. `D94`.

> ### ⚠ This is **not an audit**. It is a two-instrument disagreement in which **both** instruments have measured defects — and this repository measured both.
>
> An audit presupposes the auditor is more reliable than the audited. **Nothing here establishes
> that.** [R16](R16_selection_vs_effect/) says so explicitly: *two instruments disagreeing says
> neither is a proxy for the other; it does not rank them.*
>
> **The asymmetry that would privilege ablation is real** — ablation is *interventional*, attention is
> *observational*, and an intervention can establish counterfactual dependence where a weight cannot.
> **But this repository has measured that its own intervention is substantially off-manifold:**
>
> ```
> R6, readability = |positive control| / band sd, per arm
>                       zero    mean   resample     rr mean   rr resample
> qwen2.5-1.5b          2.35    1.03       0.77        0.44          0.33
> qwen2.5-3b           10.07    2.38       1.57        0.24          0.16
>
> median rr:  mean 0.24x   resample 0.22x        (3 informative cells, 2 of 4 rounds fully valid)
> R8: randdir's positive control SIGN-INVERTS on 4 of 4 models -- that arm is inadmissible
> ```
>
> **Replacing a head's output with its own mean, or with a resampled value, recovers only `22`–`24%`
> of what zeroing does.** So roughly three quarters of the zeroing effect is not *"this head's
> contribution"* — it is *"this activation pattern being absent entirely."* **An intervention into a
> state the model never occupies does not establish counterfactual dependence on the state it does.**
>
> **And on the other side, `D100`:** every role claim in this project — including `L22H7`'s — was
> established by **attention**. There is no third instrument.
>
> **So the honest description is:** two compromised instruments, disagreeing, with their compromises
> measured. That is a smaller claim than *"an audit"* and it is the one the evidence carries.
> `n` is small — three informative cells across four models — and that is stated rather than smoothed.

> ## ⚠ STATUS: **EXPLORATORY AUDIT — frozen 2026-07-28.** Not a confirmatory result.
>
> Everything below is a **case study on one synthetic task and one model family**, and its central
> quantity is **not** a "noise floor". It is a *conditional reference distribution* that mixes at
> least five different things — measurement error, true component heterogeneity, the generic cost of
> ablating anything, the baseline of the *selection procedure*, and task specificity — and it changes
> with layer, position, `k`, metric, and intervention support.
>
> **The scalar `2σ` floor is retained only as the historical object under audit.** With excess
> kurtosis `+7.43` it is not a normal-theory threshold, and *"beyond 2 sd"* means only *"outside a
> coarse scale of this particular reference population"*.
>
> **The confirmatory experiment this repository points at has not been run.** It is
> [`R19`](R19_crossed_position_support/PREREGISTRATION.md): a crossed *position × intervention-support*
> exhaustive scan. Until it lands, **no head-level statement here is confirmatory**, and every one of
> them is about a **final-query head-output knockout**, written `I_final(L,h)`, not about "a head".

```bash
git clone https://github.com/ivanicu/AblationNoise.git && cd AblationNoise && make verify
```

> `make verify` is **computational verification** — files exist, hashes match, every prose number
> recomputes, no detector fires. **It is not evidence for any causal claim.**

**Every number in this repository is recomputed by that command** — no GPU, no model download, no
network, no dependencies, `41.3 s` on a stock `python3` with `numpy` confirmed absent. **Verified to
run on `3.11` and `3.14`** — see `D112`, which is why that sentence now names versions. It was run
from a fresh clone of this remote on 2026-07-28, not asserted.

> **⚠ `D106`: that number was `2.6 s` for many steps and the page kept saying so while the handle
> grew `16×`.** Re-measured `41.26 s`, peak `38 MB`. The cost is the randomization tests added since:
> four `50,000`-replicate matched-layer nulls plus an `80,000`-evaluation calibration loop. **`2.6 s`
> was measured once, on 2026-07-28, against a version that had none of them** — the same
> measured-once-never-re-measured failure this repository documents elsewhere. The trade is stated
> rather than hidden: every randomization test that makes a claim checkable also makes the handle
> slower, and the correct response was to re-measure, not to cut replicates and move the numbers.

## A scalar floor does not transport — and that, not the eight heads, is the result

Transport one configuration's **whole decision rule** — `|x − mu_A| > floor_A` — into three others,
each differing from `A` in **exactly one** factor, and compare what it says against what that
configuration's own reference class says.

```
configuration                        own floor   own    A-rule   ratio    differs by
A  I_final @ unshuffled                 0.4870  10/168  10/168    1.00    (same) POSITIVE CONTROL
D  I_final @ unshuffled, NEW items      0.4891  10/168  10/168    1.00    item sample only
C  I_all   @ unshuffled                 0.9766  14/168  33/168    2.36    intervention support only
B  I_final @ SHUFFLED                   0.4023  12/168   6/168    0.50    task / answer position only
```

**Row `D` is the positive control and the discriminator.** A completely fresh item draw — seeds
`3400`–`3800` against `3000`–`3400` — transports at ratio **`1.00`**. The instrument *is* stable in
the way [R11](R11_instrument_noise/) established, **so a failure on the other rows cannot be blamed
on sampling noise.**

> **The two failures point in opposite directions.** Believing `A`'s floor under a different
> **intervention** calls `33` of `168` heads distinguishable where that configuration's own reference
> says `14` — the rate inflates `2.36×`. Believing it under a different **task** calls `6` where its
> own reference says `12` — you miss half.
>
> **A scalar floor is not merely imprecise. Its bias depends on which way the configuration moved,
> so no safety factor fixes it.**

### It is the **scale** that fails to transport, not the centre

Transporting `mu_A` and `floor_A` together cannot say *which* of them fails to travel — and the two
have completely different remedies. A local re-centring is cheap; a local **scale** means the floor
is not a number you can carry at all.

```
configuration              own   both   scale only   centre only    mu ×   floor ×
A  I_final @ unshuffled     10     10           10            10    1.00      1.00
D  I_final @ new items      10     10           10            10    1.01      1.00
C  I_all   @ unshuffled     14     33           32            12    1.98      2.01
B  I_final @ SHUFFLED       12      6            5            13    0.82      0.83
```

**`scale only`** = re-centre on the configuration's own `mu`, keep `A`'s floor.
**`centre only`** = keep `A`'s `mu`, use the configuration's own floor.

> **Re-centring fixes nothing** — `C` stays at `32` against its own `14`, `B` at `5` against `12`.
> **Using the local scale fixes almost everything** — `C` lands at `12` against `14`, `B` at `13`
> against `12`.

**And the confound written before the test is refuted in the useful direction.** `mu` and `floor` are
not independent, so a "centre-driven" verdict could have been a spread effect wearing a location
mask. Here it is the reverse: **the centre moves by almost exactly the same factor as the scale**
(`1.98×` against `2.01×` for `C`) **and it does not matter**, because the centre is roughly `10%` of
the half-width (`0.0946` against `0.9766`). Shifting it barely moves a threshold sitting at `±floor`.

**The scale is the estimand.** That is a sharper claim than *"a scalar floor does not transport"* and
it is the one the data supports.

### The fourth axis — **layer band** — fails in *both* directions, and it scopes the claim above

The layer axis was never in the table, and it carries the largest variation in the repository. It is
also the only axis where the **reverse** direction is testable, because both regions come from one
result file.

```
sham L0-7  judged by the BAND's rule :   0  against its own   4    ratio 0.00   you see NOTHING
band L14-27 judged by the SHAM rule  :  78  against its own  10    ratio 7.80   46% of the band

floor ratio band/sham  6.15x        mu ratio  12.05x
```

**And it corrects the section above.** *"The centre is ~`10%` of the half-width, so it does not
matter"* was measured **on the band**. Here `centre only` gives `8` against its own `4`.

```
                              |mu_dest − mu_src| / floor_dest    centre-only ratio
D  I_final @ new items                    0.1%                        1.00
B  I_final @ SHUFFLED                     2.2%                        1.08
C  I_all   @ unshuffled                   4.8%                        0.86
sham L0-7  (layer axis)                  55.5%                        2.00
```

> **The centre matters exactly when its *shift* is large relative to the *destination's* scale.**
> Below `~5%` the centre-only transport is calibrated (`0.86`–`1.08`); at `55%` it doubles.
> **So *"the scale is the estimand"* is itself scoped** — it holds where the centre shift is small
> against the destination scale, which is three of these four axes and not the fourth.

`n = 4` contrasts. What makes four points worth stating is that there is a **mechanism**, not just a
trend: a threshold sitting at `±f` is insensitive to a shift that is small relative to `f`, and stops
being insensitive when it is not.

### Is the conditionality an artifact of **off-manifold zeroing**? — no, and the on-manifold arms are *more* conditional

`D101` established that zeroing is roughly `4×` off-manifold. That threatens everything above: if the
floor's conditionality is a property of *zeroing* rather than of *ablation*, the headline is a claim
about one intervention, not about ablation baselines. **`R6` already has the on-manifold arms on four
models**, so the layer axis can be re-run under all three.

```
band_floor / sham_floor         zero        mean     resample
internlm2-1.8b                  0.98        2.81         2.64
phi-3.5-mini                   12.27     2132.73      2046.29
qwen2.5-1.5b                    4.31      815.46      1144.26
qwen2.5-3b                      6.73      125.10       113.21
```

**On `4` of `4` models the on-manifold arms are *more* layer-dependent than zeroing, not less.** The
conditional-reference-distribution claim **survives the off-manifold objection.**

> **But the mechanism is not established, and it must be named.** The on-manifold sham floors collapse
> to `1e-5`–`4e-6`, which [R6](R6_intervention/) already flagged as `DEGENERATE`. So *"early-layer
> heads contribute nothing recoverable and only zeroing's shock produces a signal there"* and *"the
> on-manifold arms lack the dynamic range to resolve early layers"* **are the same observation stated
> with different attitude, and nothing here separates them.** `UNVERIFIED`, not confirmed.

**And one model dissents on the zero arm.** `internlm2-1.8b`'s ratio is `0.98` — band and sham floors
are the *same* under zeroing. **So "the floor varies with layer" is `3` of `4` models, not `4` of
`4`**, and internlm2 is the model whose sham region was already flagged as non-inert.

**Two estimators of the same quantity disagree and both are reported.** `R6`'s `4.31` for
`qwen2.5-1.5b` is a `k=1` estimate from `30` draws over `12` heads; the `6.15` used earlier on this
page is **exhaustive** over every head in each region. Same intended quantity, different sampling —
which is the `R1`→`R10` story again, and neither is presented as the number.

### An outside critique of `R6`, **measured** rather than accepted — one half refuted, the other bounded

The critique: *`displacement_ratio` = `‖x−x̄‖ / ‖x‖` cannot say whether mean-ablation is near-identity,
because a small displacement can lie along an extremely high-gain direction of `W_O`, and a large one
can land in its approximate nullspace.* **Both halves are checkable from the weights alone — no GPU,
no activations.**

For a per-head displacement `d`, the functional version is `r_out = ‖W_h d‖ / ‖W_h x‖`, and since
numerator and denominator pass through the same block,

```
r_out / r  ∈  [ 1/κ_h , κ_h ]        κ_h = cond(W_h),  W_h = W_O[:, h·128:(h+1)·128]
```

```
168 band heads, each block 1536 × 128

condition number   min 2.82   p25 4.31   median 5.86   p75 7.61   max 17.67  (L27H10)
stable rank        (Σσ)² / (Σσ²)   median 117.2 of 128 dimensions
```

| the critique's two halves | verdict |
|---|---|
| *"the displacement may land in `W_O`'s approximate nullspace"* | **refuted, measured** — stable rank `117.2` of `128`; there is essentially no nullspace to land in |
| *"a small displacement may lie along a very high-gain direction"* | **bounded, measured** — the error is at most `5.86×` at the median and `17.67×` at worst |

**So `displacement_ratio` is not a sufficient statistic for functional displacement, and the critique
is right about that — but the magnitude is bounded at roughly `6×` rather than unbounded.** `R6`'s
own verdict was already `UNDECIDABLE`; this does not change it, **it explains part of why.**

> **`[1/κ, κ]` is a worst case over *arbitrary* directions and is therefore loose.** The real
> displacement is item-to-item variation of a live activation, which most likely lies in the
> high-variance directions rather than an adversarial one. **Tightening it needs the activations,
> which were never stored** — `R6`'s diagnostic file keeps `mean_norm`, `sd_norm`, `cv` and
> `displacement_ratio` only, over `L14`–`27`.
>
> **The same absence closes a question from the section above:** whether the on-manifold arms' sham
> collapse means *"no contribution"* or *"no resolution"* cannot be settled from disk either, because
> that diagnostic never covered `L0`–`7`. `UNVERIFIED` there is now **checked** as unverifiable from
> current data, not merely asserted.

### The repository's own mandated method **cannot answer its own surviving question** at this `n`

`10 of 168` is the last positive count on this page and it is a `2σ` number — on a distribution the
page itself says `2σ` does not test, at excess kurtosis `7.31`. So: recompute it with the empirical
conditional randomization percentile the repository now mandates, leave-one-out.

```
minimum attainable p from an empirical null over 168 values   1/169 = 0.0059
Bonferroni at alpha 0.05 needs                                0.05/168 = 0.00030   UNREACHABLE
BH-FDR at alpha 0.05                                          0 discoveries
uncorrected empirical p <= 0.05                               8 of 168
the published 2-sigma count                                   10 of 168
```

**Look at the p-values themselves.** The eight smallest are `0.0060 · 0.0119 · 0.0179 · 0.0238 ·
0.0298 · 0.0357 · 0.0417 · 0.0476` — that is `1/167, 2/167, 3/167, …`. **An empirical null built from
the population being tested converts every p-value into a rank divided by `n`.** The test has no
resolution beyond ordering.

> **So the mandated method cannot support any multiplicity-corrected per-head claim at this sample
> size, and `0 discoveries` is a RESOLUTION LIMIT, not an absence.** The floor was computed before
> the test and is what makes it interpretable: no family-wise-corrected test on this null can fire,
> whatever the data says.

**The set-level test does have resolution**, and the difference is instructive: its null is
*generated* by `50,000` matched-layer resamples rather than *being* the population, so it can return
`p = 0.0296` for a single head and `p = 0.6817` for the set. **Per-head significance needs a
resampled null or a larger reference class; the count-at-a-threshold does not.**

**The precise status of `10 of 168`:** a **descriptive** count at a chosen threshold on a heavy-tailed
distribution — `8` under the repository's own preferred uncorrected method, `0` under any correction,
where `0` is an artifact of `n`. **This does not touch the transport result above**, which compares
counts under a *fixed* rule across configurations and never claims per-head significance.

### Three instruments, three edges, **none positive** — and one of `R16`'s two numbers was a layer artifact

The repository had measured **one** of the three pairwise relationships between its instrument
classes and called the result *"no arbiter"*. That rested on a single edge. All three are now closed.

```
edge                                   pooled Spearman    within-layer mean
attention.name_att x ablation.I_final      -0.3952            -0.4341
attention.name_att x ablation.I_all        -0.3226            -0.3427
attention.room_att x ablation.I_final      -0.1885            +0.0060   <- vanishes
attention.room_att x ablation.I_all        -0.1806            +0.1289   <- reverses
attention.room_att x OV.rooms              -0.2124            -0.1788
attention.name_att x OV.rooms              -0.0726            -0.0425
OV.rooms   x ablation.I_final              +0.0618            -0.0914
OV.rooms   x ablation.I_all                +0.0954            -0.0345
OV.objects x ablation.I_all  (signed)      +0.2171            +0.0430
```

**⚠ This narrows `R16` by half.** Its headline was *"attention and ablation anti-correlate at `−0.19`
and `−0.40`"*. **Within layer the room-attention edge is `+0.006` and `+0.129` — it does not survive.**
Only the **name**-attention edge holds, and it holds strongly (`−0.43`, `−0.34`).

> **⚠ `D113`: those numbers were computed without the final `RMSNorm`'s learnable scale, and the
> counts move.** `model.norm.weight` spans `2063×` (`0.0043` to `8.875`) and multiplies the
> unembedding side — it is the basis the logits are actually read in. **The `1/‖x‖` half of `RMSNorm`
> is a per-destination scalar shared across all sources and cannot reorder anything; only `g` can.**
>
> **The ranking is robust** — Spearman `+0.9839` / `+0.9952` / `+0.9926` between the two bases — so
> `D108`, `D110` and `D111` are **not** in a materially wrong basis. **But the absolute counts nearly
> double**: perfect-wins goes `16 → 25` on rooms, `6 → 11` on objects, `3 → 7` on persons, and
> **`L17H0` moves from rank `3` to rank `11`.** The scaled basis is now primary and both are stored.
>
> **What survives unchanged:** `L22H7` at `140` / `136` / `149`, and `L16H3` near the bottom.

**And `attention.room_att × OV.rooms = −0.2124`, surviving the within-layer control at `−0.1788`:**
attention to the room token **anti-correlates** with the OV circuit's ability to copy the room token.

> **The three ways this literature identifies a copy head — *it attends to the thing*, *ablating it
> hurts*, *its OV maps the thing to itself* — are mutually uninformative or mildly opposed here.**

**The correct scope, which is narrower than it looks.** Three instruments disagreeing does **not** mean
all three are wrong. A head can attend to `X`, not copy `X` *directly*, and still matter causally
through composition — **disagreement is exactly what a compositional mechanism predicts.** What
follows is only that **on this task these three operationalizations do not identify the same heads,
so none of them alone licenses the phrase *"the copy head"***. Each is also a *specific*
operationalization — `E132`'s final-position attention, zero-ablation at the final or all positions,
direct-path `OV` — not "attention" or "ablation" in general.

**Both gauge checks ran:** signed *and* magnitude correlations for the `OV` edge (`D82`'s lesson), and
a within-layer control on every edge — which is what caught the `R16` narrowing.

### ⚠ The meta-separator, stated once: **there is no ground truth here, and that limits everything above**

Two checks, both cheap, both aimed at the section above rather than at the eight heads.

**1 · The failure is not about `2σ`.** Transporting an *absolute* cutoff gives a count that depends
only on the destination's distribution, so two source rules that agree on `A` must agree everywhere.
They do:

```
config              by 2sd_A   by A's 5.95th-percentile cutoff   own 2sd
D  new items              10                                 8        10
C  I_all                  33                                32        14
B  SHUFFLED                6                                 5        12
```

**So *"a scalar floor does not transport"* is trivially true of any absolute cutoff whenever the
destination distribution differs.** The section above was written more dramatically than that. What
is *not* trivial, and is what the table actually shows:

* it transports **perfectly across item samples** (`10` against `10`, ratio `1.00`) — **that is not
  automatic**, and it is what makes the other rows interpretable;
* the **magnitudes and directions** — `2.36×` inflate, `0.50×` deflate, `7.80×` and `0.00` on the
  layer axis;
* the **scale/centre decomposition** and the `|Δmu| / floor_dest` predictor.

**2 · And the question presupposes something this repository cannot supply.** *"Does the floor
transport"* assumes there is a right answer to *"how many heads are real."* **There is none here.**
Transport a **procedure** instead of a **number** — *"take the top `5.95%` of the local band"* — and
it returns `5.95%` in every configuration by construction. **It cannot fail, and it cannot be
validated either.**

> **"Calibration" in this repository means self-consistency, not correctness.** Nothing on disk
> separates *the floor is conditional* from *we have no way to know what the floor should be.* Those
> are different worlds and this design cannot tell them apart.
>
> **What would:** a case where the causal set is known — a synthetic model with a constructed
> ground-truth circuit, or heads whose role is established by an independent method (path patching,
> transduction, causal scrubbing) rather than by the same magnitude statistic being audited.
> **That experiment is not in this repository and is not scheduled.**

**What this is not:** the `own` column is the same `2σ` rule on a heavy-tailed distribution, so this
compares **two applications of one rule**, not a calibration against a nominal `α`. That is exactly
the transportability question — which is the one being asked — but it is not a `5%` false-positive
guarantee. One model, one band `L14`–`27`, one task family, `k=1`, one contrast per axis.

### The eight were **selected, evaluated and audited on the same `120` items**

Established from the source project, not from memory:

```
e132_read_head.py:29           SEEDS = range(3000, 3300)     head SELECTION
e132b_read_head_causal.py:27   SEEDS = range(3000, 3300)     causal EVALUATION of the eight
R10_exhaustive/run.py:72       SEEDS = range(3000, 3400)     THIS AUDIT, first 120 that pass
R11 set B                            range(3400, 3800)       the ONLY independent items here
```

All three take the first items passing the same baseline-correct filter from seed `3000`, and
[R14](R14_position_vs_binding/) measured that filter as rejecting **nothing** on this task for this
model. **So selection, evaluation and audit share one item set.** Nothing in this repository had
said so.

**It cuts both ways and both are stated.** The *not enriched* null is **strengthened** — the eight
fail to beat matched-layer random sets on the very data they were chosen on, with full home
advantage. But **every head-level number here except set B is computed on the selection data.**

**On the only independent items, the shrinkage depends on the aggregation, so all three are
reported:**

```
aggregation           the eight   matched-layer null median      p
sum-ratio                0.8425            1.0180            0.0150
mean-of-ratios           0.8257            1.0085            0.0098
median-of-ratios         0.9919            1.0135            0.2769
```

**Two of three fire; the median does not.** `L16H3` and `L22H7` carry `75%` of `sum|c_A|`, which
makes the sum-ratio essentially a two-head statistic. **The set-level winner's curse is not a set
property — it is one head:**

```
L22H7 retains 0.0401 of its centred effect on independent items
    lowest of all 168 band heads, 0.0th percentile, exact one-head p = 0.0118
    band median retention  1.02
    its own layer-mates    0.59 0.94 1.00 1.01 1.03 1.05 1.10 1.10 1.10 1.17 1.22
```

**That is what the rank move `41 → 160` was, and it now has a name.** The one head here with an
independently established prior claim shows the strongest selection inflation.

> **RTM control:** regression to the mean shrinks whatever was extreme, and the eight sit **below**
> the matched-layer null median on set A. So RTM predicts they shrink *less* than random, and the
> observed direction runs **against** that prediction rather than being explained by it.
>
> **The threshold was not pre-registered and the reading is post hoc.** Identifying `L22H7` needs no
> peeking — *"the head with a prior claim"* is specified by role, not by the table — but this is a
> descriptive result, not a confirmatory one.

### The right test, run last: **the eight are not enriched, and they sit below the median**

Every earlier round compared each head, one at a time, against a **scalar** floor. That asks the
wrong question twice: it runs eight uncorrected comparisons, and its reference class does not hold
**layer** fixed. The question the audit is actually asking is

> is the **pre-specified set of eight** more extreme than a random set of eight drawn from the
> **same layers**?

```
T_pub = mean over the set of |tau_h − mu_band|
null  = replace each published head with a uniform random head FROM ITS OWN LAYER, 50,000 times

              T_pub   matched-layer null median      p     excess kurtosis
I_final      0.1154            0.1670            0.7994         7.31
I_all        0.3196            0.3991            0.6817         6.67
```

**Not enriched under either intervention — and `T_pub` is *below* the null median in both.** The
eight published heads are, on average, **less** extreme than random heads from the same layers.

> **⚠ `D105`: the null draws *with replacement* and the observed set cannot.** The eight sit in layer
> multiset `{16:1, 17:3, 18:1, 19:2, 22:1}` — **three of them in `L17`** — so a with-replacement draw
> can pick the same `L17` head twice while the published set has eight *distinct* heads. Sampling
> with replacement gives the set mean a larger variance (no finite-population correction), so **the
> null is wider than the correct one and the test is conservative.** Measured: `sd` ratio `1.031` and
> `1.045`; drawing distinct-per-layer moves `p` from `0.7994` to `0.8069` and from `0.6817` to
> `0.6917` — **both away from significance.** Both are emitted; the distinct version is correct and
> the difference changes no conclusion.

> **The instrument was checked before the null was believed.** Positive control: the actual top-`8`
> by `|centred|` is reached by only `0` of `50000` matched sets, so the test can separate. Null calibration: `200`
> random matched sets fall under `0.05` at a rate of `0.065` against a nominal `0.05`.
>
> **Layer matching is not decoration.** The eight sit in `L16`–`L22`, magnitude varies strongly with
> depth, and an unmatched null would manufacture enrichment out of nothing but where the heads live.

**Both distributions are heavy-tailed** — excess kurtosis `7.31` and `6.67` — which is why the `2σ`
floor is not a test in either arm and the percentile replaces it.

### And the descriptive picture the scalar floor gave

`L22H7` was independently established, by a prior experiment, as the copy head for this task. **[⚠ `D100`: *independent of `E132`*, yes — *independent of the INSTRUMENT CLASS*, no.
`E123` established `L22H7` by **per-head final-position attention mass**
(`e123_retrieval_source.py:10,22`), which is the same kind of instrument that selected the other
seven. There is **no** intervention-based corroboration of any head's role in this repository.]**
Knock out **every one** of the `168` heads in the studied band at the final query position, once
each — no sampling — and place the eight previously published single-head effects in that ranking:

```
the eight published heads rank    10 · 41 · 77 · 79 · 129 · 157 · 158 · 162    of 168
the proven copy head              41st  -- and 160th on a disjoint item draw of the same task
of the 10 heads that clear the exhaustive floor, published ones:   1   (L16H3, the 10th)
of those 10, ones where ablation HELPS the model:                  7
```

> **The heads this instrument flags loudest were never identified.** That is the direction the
> evidence supports, on `10` points, and it needs no threshold.
>
> **The reverse does not follow, and this page claimed it for one step.** *"Magnitude and role are
> unrelated"* is a claim about a relationship and there is exactly **one** head here with an
> independently established role. **One point is an anecdote.** **And `D100` narrows it further: that role is
> attention-established, not intervention-established.**
>
> **And `41` does not replicate** — the same head ranks `160` on a disjoint item draw, the largest
> rank move of all `168`. The direction of the qualitative claim survives; the number is not a
> property of the head.

**The full inferential path, with every correction annotated where it happened, is
[`PAPER.md`](PAPER.md).**


## Where everything is

`README.md` used to be `1091` lines carrying five different jobs at once — front page, paper,
methods, audit chronology and defect ledger. **That is an information-architecture failure, not
rigour**: a reader forming a model in the first three minutes had to walk a chronology of the
author's corrections to reach the inferential path. Split without rewriting — every section below is
the same bytes, moved.

| file | what it is | who it is for |
|---|---|---|
| **`README.md`** *(this file)* | the claim, the command, the scope, the boundary | anyone, in 60 seconds |
| [`PAPER.md`](PAPER.md) | the finding and its inferential path, with every correction annotated in place | a reader deciding whether the result is real |
| [`METHODS.md`](METHODS.md) | the rounds, the task, the intervention, the detectors, how to run one | someone reproducing or extending |
| [`AUDIT_LOG.md`](AUDIT_LOG.md) | rounds that returned `NOT MET`, and the separator runs that judged the gates | someone auditing the audit |
| [`DEFECT_LEDGER.md`](DEFECT_LEDGER.md) | the error record, exhibited rather than asserted | someone checking whether the corrections are real |
| [`ADVERSARY.md`](ADVERSARY.md) | what an adversary is predicted to overturn — **scored, and `6`–`18%` accurate** | someone who wants the author's calibration, not his conclusions |
| [`R19_crossed_position_support/PREREGISTRATION.md`](R19_crossed_position_support/PREREGISTRATION.md) | **the confirmatory experiment, not yet run** | anyone asking what would settle this |

> **The round directories are not all experiments.** `R16`, `R17` and parts of `R12` are data audits,
> estimand corrections and prose corrections that were given round numbers. **A round number implies
> a scientific increment and those did not earn one** — they are relabelled in
> [`METHODS.md`](METHODS.md) rather than renumbered, because the commit history refers to them.

## What this does not claim

* Four models, three families, one synthetic task, attention-head ablation at one or all positions.
  Nothing here is established for MLP neurons, for SAE features, for natural text, or for methods
  other than zeroing a component's output.
* The floor **values** do not transfer. The *procedure* does.
* R5's readout axis is withdrawn: each model cleared on a different column, and the mechanism
  strengths were not matched across models, so that axis is confounded rather than null.

## What is open

Not a roadmap — the questions this instrument raised and cannot yet answer, each tied to the round
that raised it. They are listed because a reader deciding whether to trust the closed results is
entitled to see the shape of the open ones.

| | raised by | what would settle it |
|---|---|---|
| **Is the floor a property of ablation or of zeroing?** | every round — all of them zero | **still open after R6 and R7,** but narrowing. R7 matched the displacement and found the ordering runs against the objection in 4 of 4 cells; it fell one valid cell short of its gate. R8 needs three valid cells and an arm (`constant_only`) that separates the two worlds R7's matrix could not |
| **Does readability transfer across models?** | R4, whose across-model verdict is `UNVERIFIED` | an order of magnitude more models. Five cannot decide it: the best of 324 admissible estimators fits three model-level parameters to four model-level observations |
| **Which readout is more readable?** | R5, whose readout axis is **withdrawn as confounded** | a mechanism-**strength**-matched design. The identified head's attention was 0.244 on one model and 0.852/0.877 on the others, so the readout comparison is confounded with mechanism quality. More models do not fix this; matched mechanisms do |
| **Does any of it hold outside attention heads?** | scope of every round | MLP neurons, SAE features, residual directions. Nothing here is evidence about them, and the two-point calibration is a hypothesis there, not a method |
| **How often does published work report a random-component baseline at all?** | the front page's original first paragraph, which asserted "almost none" with no measurement | a **claim-level** survey: decompose each paper's headline ablation claim into (intervention, control, statistic, scope) and check whether a same-size random null is reported *with its spread*. Abstract search cannot answer it — whether a null was reported is a methods detail — so an abstract-level result here would be an unfit instrument, not a weak one |
| **Does it hold off a synthetic task?** | scope of every round | a natural-text task with a known mechanism. The synthetic binding task was chosen so the answer key is not arguable, which is also why it is not a claim about language modelling |

One item that is **not** open: whether R1's number is an artifact of R1's own code. R6's zero arm
reproduced it to **0.0%** on **four models out of four**, through a completely rewritten measurement
path.

## Licence

MIT.
