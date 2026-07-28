<!-- unbacked-ok: 2.62 24 41.3 41.26 38 16 27.58 17.2 35 -- the fresh-clone verification's wall
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

# The finding, and every correction it survived

> Split out of `README.md` on 2026-07-28 without rewriting: the sections below are the same
> bytes, moved. Status, scope and the runnable command are on the [front page](README.md).

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

## The finding, as the scalar floor described it

`L22H7` was independently established, by a prior experiment, as the copy head for this task. **[⚠ `D100`: *independent of `E132`*, yes — *independent of the INSTRUMENT CLASS*, no.
`E123` established `L22H7` by **per-head final-position attention mass**
(`e123_retrieval_source.py:10,22`), which is the same kind of instrument that selected the other
seven. There is **no** intervention-based corroboration of any head's role in this repository.]**
Ablate **every one** of the `168` heads in the studied band, once each — no sampling — and place the
eight previously published single-head effects in that ranking:

```
the eight published heads rank    10 · 41 · 77 · 79 · 129 · 157 · 158 · 162    of 168
the proven copy head              41st
of the 10 heads that clear the exhaustive floor, published ones:   1   (L16H3, the 10th)
of those 10, ones where ablation HELPS the model:                  7
```

> **The direction that is supported: the heads ablation flags loudest were never identified.** Of
> the `10` that clear the exhaustive floor, `0` are in any prior experiment's list until the `10`th,
> and `7` of them clear by *helping* the model. That is `10` points, and it needs no second known
> mechanism.
>
> **The reverse direction is not supported, and this page claimed it for one step.** *"Magnitude and
> role are unrelated"* is a statement about a relationship, and this repository has exactly **one**
> head with an independently established role — `L22H7`, which ranks `41` of `168` (**and `160` on a
> disjoint item draw of the same task — the largest rank move of all `168`; the rank does not
> replicate, though the direction of the qualitative claim strengthens**) at `0.37×` the
> floor. **One point is an anecdote, not a relationship.** Five of the other seven were read-head
> *candidates*; a candidate is a hypothesis, and finding that hypotheses fail to clear a floor is
> close to tautological.

**And the zero is admissible**, which this repository's own rule requires before any null may be
reported: nine heads on the *same run* are both resolvable at `2σ` **and** beyond the floor, at
`1.18×`–`2.54×` the floor and `2.5×`–`22.1×` their own measurement noise. The instrument returns
non-zero on exactly the data that returns near-zero for the eight.

**Scope, stated because this repository requires it of every claim:** one model (`qwen2.5-1.5b`),
one synthetic task, one vocabulary, `n=120` items, `k=1`, exhaustive over `28 × 12` heads, and — see
the correction immediately below — **one prompt configuration**, because the answer always sits at
line `0`
**the floor `0.4870` was measured at baseline margin `4.477` and [is a function of that headroom](R15_shuffled_scan/README.md)**, **and the ablation zeroes the *final position only***, so the unit measured throughout is not “a head” but **a head's write at the final position** — which is a scope on every number here, and is [the reason R12's depth verdict is `UNVERIFIED`](R12_cross_model/README.md#-the-verdict-is-unverified-because-the-instrument-has-a-depth-bias-shaped-like-the-winner).

> ### This front page has been rewritten six times, and every version it replaced is still on it
>
> `almost none report a random control` → `7 of 8 sit inside the floor` → `the single head is the
> wrong unit` → `9 of 168 clear, so ablation resolves effects` → `0 of 8 distinguishable` →
> `a synthetic binding task`. **Each was killed by a cheaper computation on data already in the
> repository**, and each correction is annotated in place below rather than deleted — a page that
> shows only its current claim cannot be checked against the ones it abandoned.
>
> **The corrections are the substance of this project, not its errata.** They start immediately
> below and run to the `82`-row defect ledger at the end.

---

> # READ THIS FIRST — the task is not what twelve rounds of this repository said it was
>
> Every runner picks its query person as *the first single-token name*, and every binding assigns
> **all eight** names — so the query is **always `Alice`**. The prompt's fact lines are emitted in a
> fixed order, so Alice's fact is **always line 0**.
>
> ```
> line 0: Alice owns the wand. The wand is in the rust room.     <- the answer, every item
> line 1: Bob   owns the pill. The pill is in the rust room.
> ...    six more facts, never queried
> line 8: Question: Which room should Alice go to find their object?
>
> correct answer = rust = the room in LINE 0
> ```
>
> **`copy the room from line 0` scores `100%` without matching a single name.** The *answer* varies
> — across `400` seeds the four rooms take `23.5%`–`26.2%` — so the labels are balanced. The
> *structure* is not: **this is a fixed-position retrieval task, and it cannot distinguish
> position-copying from name-binding, because the two strategies agree on every item it contains.**
>
> **What this does not break.** Every comparison *between* heads. All of them face the same task, so
> the floor, the ranking, the counts, the item-noise and the null's centring are unaffected as
> statements about this task, and the methodological findings stand entirely.
>
> **What it breaks.** The description. `L22H7` was called a *copy head*; on this task it may be
> copying from **position `0`** rather than resolving a name, and no measurement here can tell those
> apart. Every claim below about *binding* should be read as a claim about **fixed-position
> retrieval**.
>
> **Is the degeneracy uniform across models?** It had to be: the query is the first *single-token*
> person, which depends on the **tokenizer**, so a model where `Alice` is not one token would be
> asked about someone else at a different line — and `R1`'s cross-model ratio would be comparing two
> different fixed-position tasks. Probed with the runners' own convention, tokenizers only:
>
> ```
> single-token persons   qwen2.5-1.5b 8/8   qwen2.5-3b 8/8   phi-3.5-mini 6/8   internlm2-1.8b 4/8
> distinct query LINE indices across 8 model × vocabulary cells:  [0]
> ```
>
> **Uniform.** The counts differ, `Alice` is single-token everywhere, and every model is asked about
> line `0`. The cross-model comparisons stay commensurable — **and the degeneracy is everywhere.**
>
> ### RESOLVED by [R14](R14_position_vs_binding/) — the model is **not** copying line `0`, and the implication was mine
>
> Shuffling the fact lines so the answer lands at a random index: accuracy `1.000` → `0.800`,
> against a chance of `0.25`. **Pre-registered verdict `MIXED`** (`BINDING` needed `≥0.900`,
> `POSITION` needed `≤0.350`). And the confound control, built to separate two shapes, returned a
> third:
>
> ```
> line   0     1     2     3     4     5     6     7
>       1.00  1.00  0.60  0.62  0.75  0.57  0.86  1.00      a U, not a step and not a decay
>
> ends L0,1,6,7  0.966 ±0.046      middle L2–5  0.639 ±0.121      diff +0.327,  z = +4.96
> ```
>
> **Every line is above chance**; the worst is `0.57`, which is `2.3×` chance. The task *permits* a
> degenerate strategy — that part of the finding below stands — but **the model does not use it**,
> and across two steps I let the implication that it might hang unresolved. The pre-registration
> named that outcome as a kill aimed at my own steps and required it be reported as loudly as the
> other one.

> ### Every head-level number here is measured in **one** configuration — and the obvious repair would have been run wrong
>
> [R14](R14_position_vs_binding/) showed the model's accuracy is **position-dependent**. So every
> head-level result in this repository — the `1 of 8`, the ranks, the `10` of `168` — is measured in
> one cell of a space the model demonstrably treats differently: *the answer is always at line `0`*.
>
> [R15](R15_shuffled_scan/) is the repair, and **its design defect was caught before the compute**,
> from R14's own per-item records. The exhaustive runner keeps only items answered **correctly**;
> under shuffling `24` of `120` are wrong, and which ones is position-dependent:
>
> ```
> ends L0,1,6,7   offered 49.2%  →  kept 59.4%      +10.2 points toward the easy half
> ```
>
> **The floor it produced would be the easy half's floor, with nothing in the output saying so.**
> The fix is free — drop the filter, because a `drop` is a change in *margin*, which is defined
> whether or not the argmax is correct, and on the original task accuracy is `1.000`, so **the
> filter has never rejected a single item there.** R15 is pre-registered and blocked on hardware,
> not on design.

> ### And [R12](R12_cross_model/) settled where the hump lives — a fixed **fraction** of the stack, not a fixed layer
>
> `qwen2.5-3b` has `36` layers against `qwen2.5-1.5b`'s `28`. At `28` a fixed layer *index* and a
> fixed depth *fraction* coincide; at `36` they are five layers apart. Thresholds were committed
> while the run was executing and re-derived under the centring correction **before** it produced a
> file.
>
> ```
> centroid   22.833     bootstrap 95% CI [21.52, 24.01]
> ABSOLUTE predicted 17.23   OUTSIDE the interval
> RELATIVE predicted 22.34   INSIDE  the interval        -> RELATIVE
>
> depth fraction   qwen2.5-1.5b 0.6383      qwen2.5-3b 0.6524
> ```
>
> **The shape does not transfer, and that is the more useful half.** `qwen2.5-1.5b`'s profile is a
> clean hump peaking at `83%`; `qwen2.5-3b`'s has three near-equal maxima (`56` · `50` · `50%`) and
> a dead zone across `L1`–`L11`. With `16` heads per layer a rate carries about `±24` points at
> `95%`, so **the four highest layers are statistically indistinguishable and the peak location is
> not resolved.** The verdict rests on the centroid, which averages over all `36` layers. `n=2`
> models establishes no law.

> **And the reason it took thirteen rounds:** an elaborate apparatus was built to audit
> *measurements* — `4` detectors, `62` logged defects, a pre-registration per round — and **none of
> it was ever pointed at the thing being measured.** The task's own construction was read for the
> first time in the thirteenth round, and it took twenty lines of `python` with no model loaded.

Then it points the measurement at its own author's prior results. The finding, stated at the size
the evidence supports:

> ## The heads that ablation flags loudest are not the heads anyone identified — and are mostly heads whose removal *helps*
>
> `L22H7` was independently established as the copy head for this task. Ablate every one of the
> `168` heads in the studied band, once each, and it ranks **`41` of `168`**.
>
> ```
> 10 of 168 heads clear the exhaustive floor of 0.4870 at k=1, up to 2.44×
>  1 of those 10 is a published head — L16H3, last of the ten, at 1.06×
>  7 of those 10 clear in the HELPING direction — ablating them makes the model MORE correct
>
> the eight published heads rank   10 · 41 · 77 · 79 · 129 · 157 · 158 · 162   of 168
> ```
>
> **The heads ablation flags loudest were never identified** — `10` clear the exhaustive floor and
> the first published one is the `10`th. That direction rests on `10` points and needs no threshold.
>
> **The reverse — *magnitude and role are unrelated* — is `n=1` and was claimed here for one step.**
> `L22H7` is the only head in this repository with an independently established role. See the
> correction below for what the *count* does and does not establish.
>
> *Every number in this block moved when the null was re-centred on its own mean of `+0.0479`. The
> counts read `9` and `0`; the ranks read `10 · 55 · 56 · 109 · 113 · 115 · 116 · 143` and the copy
> head `56`th. Centring reorders by `|drop − mean|` rather than `|drop|`, which is the question the
> ranking was always asking. The correction is spelled out below.*

> ### And the count `9` establishes nothing — corrected the step after it was written
>
> *"`9` of `168` clear, **so single-head ablation resolves effects here perfectly well**"* does not
> follow. Beyond `2 × sd` a **normal** distribution of `168` numbers gives `7.6` and a **Laplace**
> gives `9.9`. Observed: `9`. **The tail is exactly what a heavy-tailed distribution hands you for
> free**, and this one has excess kurtosis `+7.43`, so `2 × sd` is a normal-theory cut on something
> nothing like normal. A count of tail members is not evidence that any member is resolvable.
>
> This is [`ADVERSARY.md`](ADVERSARY.md) row **A4**, and it is the first prediction in that file to
> resolve. I rated it *"partly lands, medium severity — I do not know whether the count changes."*
> **The count does not change under leave-one-out** (each head judged by a null excluding it: still `9`). *It later moved to `10` for an unrelated reason — the null was not centred at zero — which is a different defect, corrected below.*
> **The interpretation breaks instead.** My severity estimate was too low, which is the row scoring
> me rather than the other way round.
>
> **What survives is every statement about ORDER**, because a ranking needs no threshold: the eight
> published heads at `10 · 41 · 77 · 79 · 129 · 157 · 158 · 162`, the proven copy head `41`st, and
> `1` of the top ten among them — `L16H3`, which is the tenth. Whether any individual head is *resolvable* is a question about
> measurement noise, not about the spread across heads, and it is what R11 was launched to answer.

> ### The depth control — run expecting it to kill the ranking, and it did not
>
> [R9](R9_depth_profile/) established the floor **grows with depth**, so a ranking by raw `|drop|`
> systematically favours deep heads. The eight published heads sit at mean layer `18.1`; the raw top
> nine at `21.0`. **That confound is real and it is not the explanation.**
>
> Rank every head against **its own layer's** `sd` instead, and the normalised top nine are *deeper
> still* (`21.8`). The published heads move by at most `±21` places out of `168`, and the proven
> copy head goes from `56`th to `53`rd.
>
> ```
> rank by |drop|/layer-sd     L16H3 15 · L17H0 34 · L22H7 53 · L17H11 96
>                             L17H7 99 · L18H9 127 · L19H5 134 · L19H0 154
> published among the normalised top nine    0
> ```
>
> **And the invariance is worth more than either list.** The two top-nines share only `6` of `9`
> members — *which* heads are at the top depends on the normalisation, which is one more reason not
> to treat any of them as special. That the published heads are in **neither** top nine does not
> depend on it.

> ### The symmetric error, refused explicitly
>
> Those nine heads are **not** hereby claimed to be the real mechanism. A large ablation effect is
> evidence that *removal matters*, in either direction — `7` of the `9` matter by making the answer
> **better**. Reading a big number as a role is precisely the inference this repository exists to
> refuse, and it does not become sound when the big number is one I found.
>
> What the exhaustive scan yields is a **list of heads whose removal moves the answer**. Turning
> that into a list of heads that implement the task requires the work nobody has done here.

> ### This is the third front page in three steps, and the two it replaces are kept below
>
> `all eight published effects sit inside the noise floor` → `the single head is the wrong unit` →
> the paragraph above. Each was corrected by a cheaper computation on data already in the
> repository, and each correction is annotated in place rather than deleted, because a page that
> only shows its current claim cannot be checked against the ones it abandoned.
>
> The second of the three — *"the single head is the wrong unit"* — was **wrong in the direction
> that flattered the project**: it made a limitation of the granularity sound like a discovery about
> it. Nine heads clearing the floor at up to `2.54×` says the granularity was never the problem.

### Two corrections to how this used to be worded, both predicted by [`ADVERSARY.md`](ADVERSARY.md) before they were made

This page used to lead with *"all eight published single-head effects sit inside the noise floor"*.
Writing down what a hostile reader would attack produced two rows that hit that sentence, and both
are right:

| | |
|---|---|
| **A1** | **"Eight published effects" oversells the population.** The set is `5` read-head *candidates*, `1` independently proven copy head, `2` unlabelled. A candidate is a hypothesis; finding that five hypotheses fail to clear a floor is close to tautological — R1's own set-level data puts the READ set at the `46.7`th percentile of the null, so **there was nothing there to find**. The count of *established* mechanisms shown inside the floor is **`1`**, and it is the one that matters. |
| **A3** | **`k=1` is the wrong granularity, and the repository had the stronger claim in hand.** Leading with *"published effects are noise"* was the more provocative reading of data whose honest reading is *"single heads are the wrong unit"* — because the `k=5` circuit result was sitting in the same round the whole time. |

**They were self-corrected, not tested.** A future adversary cannot score these two rows any more,
and the calibration record says so: they were written as predictions on 2026-07-28 and acted on the
same day, with the commit order as the only proof they came first.

> **The floor `L22H7`'s `0.27×` is measured against was itself audited, and it moved.** It is `2 × sd` of **30 random draws** from a band of `168` heads; [R10](R10_exhaustive/)
> measured all `168`, and the exhaustive floor is `0.4870` rather than `0.4418` — which flipped the
> count of the eight from `7` inside to **`8` inside**, since `L16H3`, the only one that had
> cleared, now sits at `0.96×`. The sampled floor is neither wrong nor lucky — it is at the
> `45.1`st percentile of its own sampling distribution — it is **unresolved**, because a 30-draw
> floor from this population spans `2.7×` from p05 to p95. **The floor had a noise floor.**
> `make headline` replays the draw from its seed and returns the recorded value with
> reconstruction error `0`, so the number is now computed rather than stored.

### Both halves are now measured, and they say opposite things about the same eight numbers

`R11` ran the same exhaustive scan twice on **disjoint item sets** and finally stored the quantity
every earlier run computed and discarded: `per_head_sem = sd_over_items / sqrt(n)`. Three readings,
all fixed in [its pre-registration](R11_instrument_noise/PREREGISTRATION.md) before either job left
the queue.

```
head        drop     2*SEM    |drop|/2SEM     x floor    rank A   rank B
L16H3    -0.4668    0.0334       13.97          0.96        10       10
L17H0    +0.1336    0.0295        4.52          0.27        55       50
L22H7    -0.1317    0.1040        1.27          0.27        56       96   <- the proven copy head
L18H9    +0.0410    0.0144        2.85          0.08       109      108
L17H11   +0.0379    0.0092        4.10          0.08       113      109
L19H5    +0.0373    0.0035       10.53          0.08       115      115
L17H7    -0.0352    0.0082        4.31          0.07       116      116
L19H0    +0.0154    0.0033        4.64          0.03       143      144

RESOLVABLE at 2σ      8 of 8            DISTINGUISHABLE from a random head      1 of 8
   on a disjoint item set:  7 of 8
```

> ### The `8 of 8` does not fully replicate — and the head that flips is the copy head, for the third time
>
> `8 of 8 resolvable` was computed on the **published** item set and stated without that scope. On
> the **disjoint** set it is **`7` of `8`**: `L22H7` goes `1.27×` → `0.57×` and crosses the line.
> Every other head is stable and far above `1`.
>
> **The instrument replicates; this one head does not.** Across all `168` band heads the two runs
> agree on `157` resolvability verdicts (`93.5%`) with Spearman `+0.9825` between the ratios.
>
> **That is the third independent signature on the same head.** Its rank moved `40` places between
> item sets while every other published head moved `≤5`; it is the band's worst
> SEM-versus-disagreement case; and it is the only one of the eight whose resolvability verdict
> flips. **The one head with an independently established role is the one whose ablation effect is
> least reproducible across items** — which is what an item-dependent mechanism should look like,
> and is the opposite of how a large ablation number is usually read.

> ### CORRECTED — the null is not centred at zero, and every verdict here assumed it was
>
> `distinguishable` was `|drop| > 2·sd`, which silently places the null at `0`. **The studied band's
> mean drop is `+0.0479` — `0.20` sd.** Ablating a random late-layer head *improves* the
> correct-answer margin more often than it hurts: **`100` positive, `68` negative of `168`.** **[⚠ that split is RAW; centred on the band mean `+0.0479` — the statistic every verdict in this repository actually uses — it is `64` above and `104` below, and the qualitative reading inverts. `D90`.]** A head
> that does nothing therefore sits `0.0479` away from the null's centre, and the question *"is this
> head unusual among random heads"* is `|drop − mean| > 2·sd`.
>
> **It changes the count.** `L16H3` goes `0.96×` → **`1.06×`, clearing**, so the correct figure is
> **`1` of `8`**, not `0`. The proven copy head moves the other way, `0.27×` → `0.37×`, and stays
> far inside. Across all `168` band heads the clearing count goes `9` → `10`.
>
> **And the offset had to be shown not to be an intervention artifact before the centred statistic
> could be trusted.** If zero-ablating *any* head nudged this readout upward, `+0.0479` would be a
> property of the operation, not of the band. The **sham band is centred** — `+0.0040`, `0.10` sd, a
> `51/45` sign split — while the studied band is at `0.20` sd. The offset grows with depth alongside
> the spread. **It is a fact about the late band, not about zeroing.**

> ## Every one of the eight is measurable. Not one of them is special.
>
> **The measurement was never the problem.** Being *resolvable by the instrument* and being
> *distinguishable from a random component* are different properties, and the second failed for
> **seven of the eight** — including the head independently proven to implement the behaviour, which
> sits at `0.37×` of the floor. The eighth, `L16H3`, clears by `6%`.

> ### Which null? The choice moves the floor `6.15×`, and the pre-registered test did not fire
>
> `distinguishable` is measured against the **studied band's** own heads. A defensible rival null is
> the **sham band** — layers `0–7`, heads presumed not to implement this task, which is what
> [R1](R1_noise_floor/) originally used. R10 measured all `28` layers, so the comparison was free.
>
> ```
> studied band  L14–27   n=168   floor 0.4870
> sham band     L0–7     n=96    floor 0.0792      6.15× apart, from reference class alone
>
>              x band   x sham                       x band   x sham
> L16H3          0.96     5.90  clears sham         L17H11     0.08     0.48
> L17H0          0.27     1.69  clears sham         L19H5      0.08     0.47
> L22H7          0.27     1.66  clears sham         L17H7      0.07     0.44
> L18H9          0.08     0.52                      L19H0      0.03     0.19
> ```
>
> **Pre-registered before running: `≥4` of `8` clearing the sham floor would mean the reference
> class decides the verdict. Observed `3`. It did not fire**, so that claim is not made.
>
> **But the shape is sharper than the threshold it was testing.** `78` of the `168` band heads —
> **`46%`** — also clear the sham floor. Clearing it is not a mark of distinction.
>
> **And "late-layer" was too coarse — corrected the step after it was written.** The fraction of a
> layer's heads that clear the sham floor rises with depth (Spearman `+0.645` over `28` layers) but
> **not monotonically**: it peaks at `83%` in `L16–L17` and falls back to `8%` by `L25`. `L25`
> clears *less* often than `L11`. It is a **hump**, not a half, and the earlier wording — *"being
> in the second half of the network"* — described a monotone rise that the data does not show.
>
> ```
> L0–7    0–8%        L11–14   33–42%       L18–22   42–58%
> L8–10   8–17%       L15–17   67–83% ←peak L23–27    8–42%
> ```
>
> > **`L22H7` is distinguishable from an early-layer head and indistinguishable from a late-layer
> > one. Its ablation number carries *depth* information, not *role* information.**
>
> Two facts place it exactly. `L22`'s own clearing rate is `42%` — the band average — and **within
> that layer the proven copy head is the `5`th of `5` heads that clear: the smallest one.** And
> `4` of the `8` published heads live in `L16–L17`, the **peak** layers where `83%` of heads clear —
> which is why those four clear the sham floor, and why it establishes nothing about them.
>
> Both floors are defensible and answer different questions. The front page's verdict is against the
> band floor — *is this head special among the heads I might have picked instead?* — and it stands
> at `1` of `8` (`0` before the null was re-centred). The sham comparison answers *is this head in
> the second half of the network?*, and
> the eight answer it the same way `46%` of the band does.

> ### The positive control for that zero — which this repository required of itself and had never supplied
>
> `7 of 8 inside` is a **measured near-zero** — it was reported as `0 of 8` clearing until the null
> was re-centred — and this project's own rule is that a measured zero is
> **inadmissible until the same instrument has returned non-zero**. A null from an instrument that
> has never produced a positive is silence, not an acquittal. That control was never stated.
>
> **It passes, and it was sitting in the same run.** Nine heads are *both* resolvable at 2σ *and*
> beyond the exhaustive floor — `1.18×` to `2.54×` the floor, `2.5×` to `22.1×` their own `SEM`.
> The instrument returns non-zero on exactly the data that returns zero for the eight.
>
> **And the design has the dynamic range**: for `167` of `168` heads the floor exceeds that head's
> own measurement noise, so "measurable *and* distinguishable" is achievable in principle for
> nearly every head. **The exception is named rather than averaged away** — `L26H7` has
> `2·SEM = 0.4991` against a floor of `0.4870`, so its own item-to-item variance exceeds the entire
> between-head spread and **no verdict about it is possible at all**. One head, stated.
>
> **It is also not a landslide, and saying so is part of reporting it.** The largest published
> effect reaches `96%` of the threshold; the second reaches `0.27×`. One head just missed and seven
> are nowhere near.

**The denominator is trustworthy, and that was checked rather than assumed.** If item sampling were
*not* the whole story, the SEM would understate the noise and `8 of 8` would be inflated. Across the
`168` band heads, run-to-run disagreement lands inside the SEM-predicted band **`164` times —
`97.6%`, against the `95.45%` a 2σ band is built to give.** Nothing unmodelled is left over.

**The pre-registered kill did not fire.** Exhaustive floors on the two disjoint item sets: `0.4870`
and `0.4891`, a `0.4%` divergence against a `20%` threshold. That is *not* evidence the floor is
item-set-independent — `n=2`, and [R4's lesson](R4_predictability/) is that two points establish no
law. It is one comparison that did not fire.

**And the ranking is stable across item sets:** Spearman `+0.9778` over `168` heads, top-nine
overlap `9 of 9`, `0` published heads in either top nine. That was the last free variable in the
rank claim and it is now closed.

> **⚠ THOSE THREE NUMBERS ARE UNCENTRED, AND THIS PAGE'S RANKS ARE CENTRED (`D87`).** Ranking by
> `|drop|` puts the null at zero — the same defect corrected in `R1` and again in `R2`, a **third**
> instance — so the round validating these ranks computed a ranking this repository does not use.
> Recomputed on the centred statistic the page actually reports:
>
> ```
>                        Spearman   RMS rank disp   largest mover
> uncentred (as above)    +0.9778       10.22        L23H3    43
> CENTRED  (this page)    +0.9570       14.23        L22H7  −119
> top-nine overlap        7 of 9,  1 published head in B's top nine
> ```
>
> **`L22H7` moves `41 → 160`, the largest move of all `168` heads.** The list as a whole is still
> stable — median displacement `4`, 90th percentile `17` — but *the one head carrying the
> load-bearing claim is the exception*, and by three times more than this paragraph said.

> ### The exception is the copy head, and it points the other way
>
> Every published head moves by `≤5` places between item sets. **`L22H7` moves `40`** — and
> reading 2 independently flags it as the band's worst SEM-versus-disagreement case. It is the
> single least item-stable head among the eight, and it is the one with an independently
> established role.
>
> **A copy head's contribution depends on *which* object is being copied, so item-dependence is
> what it should look like.** Its instability is evidence *for* item-dependent machinery, not
> against it — which is the opposite of how a large ablation number is usually read. `n=2` item
> sets and one head: an observation, not a finding.

> ### RETRACTED — the free bound this replaces was wrong in method AND in answer
>
> Two steps ago the item-noise floor was inferred from the **quietest layer**, giving *"`3` of `8`
> measurable"*. It was withdrawn the following step because a quiet layer is quiet in **both**
> terms — Spearman between a layer's mean `|drop|` and its spread is `+0.962`. Measured directly,
> the answer is **`8` of `8`**. The bound did not merely rest on a bad assumption; **it also got
> the number wrong**, and in the direction that made the instrument look weaker than it is.

**A second, independent split — this one at the SET level.** The measurable/distinctive axis above
is about one head at a time. Ablating the *sets* and placing them against a 30-draw set-size null
separates a different pair:

```
COPY circuit, 5 heads    −1.428     0.0th percentile of the null   invisible alone, enormous together
READ candidates, 5 heads +0.088    46.7th percentile               indistinguishable from 5 random heads
```

For the copy circuit it **is** a resolution limit — the effect is there and k=1 cannot see it. For
the read candidates there is **no hidden effect to resolve**: five of them together do what five
random heads do. A single-head result inside the floor is therefore `UNVERIFIED`, never
"unreadable", and the cheap way to tell which is to ablate the set.

**And the whole k=1 comparison is sub-behavioural.** The answer flips exactly when the margin
reaches zero, so the distance to a behavioural change *is* the baseline margin. Measured against
it:

```
baseline margin            4.477    the whole distance to a different answer
the floor (2 sd, k=1)      0.442     9.9% of it
the largest of the eight   0.467    10.4%
the copy head L22H7        0.132     2.9%

at k=5 the null's full range 2.482   55.4%   — this regime does reach behaviour
```

Across all models the k=1 floor is **at most 16.7%** of the distance to a flip. So at k=1, on this
task, **both the signal and the noise live inside a tenth of the way to the model answering
differently** — the comparison is real, and it happens entirely in a regime where the task outcome
never changes. That is the fourth scope (*regime*) this repository requires of every claim and had
never answered for its own headline.

**No independent reviewer has seen any of this.** Every claim is `[unchallenged]` — which is not the
word *clean*, and [`ADVERSARY.md`](ADVERSARY.md) says why: a reviewer drawn from the same weights as
the author can only attack what the author already anticipated. That file predicts, in rank order
and **before** the fact, what a hostile clean-context reader will find, so that when one runs its
findings score the author's model of his own blind spots. Two of its eight rows argue that this
front page overstates its own result.

**Writing the predictions found four defects on its own**, all in the detectors: the checker covered
`11` of `27` markdown files; one `>` inside an exemption comment silently disabled the whole
exemption; an exemption written in scientific notation exempted nothing; and the gate's own
false-pass rate had grown `41%` in a single session purely from the repository getting bigger.

Everything here runs on one consumer GPU. Every round is pre-registered with a kill condition
committed **before** the run. **Six of the seven completed rounds killed, withdrew or failed to
reach the hypothesis their author preferred** — one had its verdict withdrawn by the round after it,
one was defeated by a diagnostic its author wrote to attack it, and one found two of its own
pre-registered worlds had identical predictions.

> ### RETRACTED 2026-07-28 — the first sentence used to claim *"almost none report what a random component does"*, and that is **false**
>
> It was a proportion over an unbounded corpus, stated as fact, with no measurement behind it, on
> the front page of a project whose subject is claims stated as fact. It had no executable
> falsifier, so by this repository's own rule it could never have been more than D4. **One arXiv
> query refuted it.**
>
> Ten of the ten relevant papers returned report a random-component control, several as required
> methodology:
>
> | | |
> |---|---|
> | `2605.24059` | *"group ablation against a **matched-random control** completes the causal claim"* — a recipe step |
> | `2606.05378` | *"the matched-random null **sampled across ten seeds per cell**"* — a distribution, not a draw |
> | `2605.29126` | *"indistinguishable from the angle between two **random subspaces** (the Haar-uniform null)"* |
> | `2605.00333` | a layer-matched negative control, a **hypergeometric null**, and permutation tests |
> | `2607.01002` · `2604.01094` · `2603.11793` · `2606.09607` · `2607.04167` · `2607.18921` | random-heads, random-direction and layer-matched controls |
>
> **The sampling is biased and that bound is stated, not hidden:** the query contained the word
> *random*, so it selected for papers that report one. **This sample can refute a universal
> negative and cannot estimate a base rate.** What it establishes is that the practice exists, is
> current, and is treated as standard in at least one active programme — which is enough to kill
> *"almost none"*.
>
> ### AND THE FALLBACK CLAIM WENT TOO — *"nobody characterises the floor's properties"*, also false
>
> The retreat above was to a narrower claim: fine, the practice exists, but **what that baseline is
> like** — layer dependence, per-model variation, its spread — is uncharacterised. A first query
> aimed at that returned zero papers *and none of the ten above*, so it was recorded as
> **UNVERIFIED**: an instrument that cannot retrieve its own known positives returns silence, not
> absence. Abstracts were the wrong instrument anyway — whether a null was characterised is a
> **methods** detail.
>
> Reading the methods sections settled it. **This is not the earlier silence promoted to a verdict;
> it is a different instrument returning content.**
>
> | the property | where it already is |
> |---|---|
> | the null's **spread**, not just its mean | `2606.05378` §6 reports every cell as `mean ± std` over ten seeds |
> | **layer dependence** of the null | same §6: *"L0-concentrated screens **cannot use same-layer matched-random as a tight null**"* — `−57.5 ± 18.1pp`, so a screen at `−80.5pp` is only `1.4×`, and *"removing any 5 of them is destructive regardless of which 5"* |
> | a **per-model** noise floor | `2605.24059` §3.5 is titled *"Null-selectivity as a per-model noise floor"* — the null drawn **500 times per model**, `null_p99` used as the threshold |
> | **scope-limiting** a floor-derived number | same §3.5: their conserved fraction is *"best stated as within-family-and-scale rather than universal"* |
>
> **So the floor is not this repository's object, and neither are its properties.** Two consecutive
> retreats, both refuted, is not four bad sentences — it is the same error twice, and it has a name:
> *what comes easily to me came easily to everyone.*
>
> **What is left, stated at the size the evidence supports.** Two things were absent from the four
> sections read — and *absent from four sections* is the entire claim, not a claim about the field:
> those papers hold **k fixed** (§6 sweeps *seeds*, not set size) and report the null in **raw
> percentage points** rather than as a dimensionless `sd(null)/|baseline margin|` that compares
> across models. Eight of the ten papers remain unread.
>
> And one thing is structural rather than novel: every control in those papers certifies **its own
> paper's screen**. This one is pointed **backwards, at eight already-published effects** that were
> reported without it — where the null had been **a single draw at the 96.7th percentile** of the
> proper distribution. That is an audit, not an instrument. It is the honest description.

```bash
make verify     # 5 selftests + the attack suite, 73 recomputed numbers, 28 markdown files
make headline   # just the numbers, recomputed from the checked-in results
```

**No GPU, no model download, no network, and no dependencies** — and on 2026-07-28 that was
**tested rather than asserted**, from a fresh clone of the published remote, on `/usr/bin/python3`
with `numpy` confirmed absent:

```
git clone https://github.com/ivanicu/AblationNoise.git && cd AblationNoise && make verify

5 detector selftests    PASS          provenance      49 result files audited
attack suite            6 of 6 refuse recomputed      73 numbers
markdown files          28 of 28 fully backed         2.62 s, 24 MB
(that 2.62 s is the 2026-07-28 fresh-clone measurement; the handle now takes 41.26 s -- D106)
```

> **That run also shows `0 CONFIRMED` on provenance, and that is the honest state rather than a
> bug.** Every runner's `_PRODUCER` field was changed the same day — it had recorded a *basename*
> that eleven rounds share — so no existing result's stamp matches its runner's **current** source.
> Three resolve against an **earlier** committed version and say so; the rest predate stamping.
> **Re-stamping without re-running would be a lie**, because the results were produced by the code
> that existed then. The mismatch is left visible and explained.
>
> **And the gate weakens as the repository grows.** The detector's false-pass rate is `27.58%`
> against the `35%` ceiling that fails the build; it was `17.2%` two sessions ago. Every generator
> added to strengthen the gate widens the reference set and weakens this check — which is why the
> figure is printed on every run instead of being inferred.

`make verify` runs in about two seconds. That is deliberate: a repository
whose subject is *whether you can check a claim* has no business requiring a scientific stack before
you can check its own. (Reproducing a *round* needs `torch` and `transformers`; verifying the
**claims** needs neither, and the two paths are separate targets.)

`make verify` exists because this repository has twice caught **itself** shipping a number that
could not be regenerated — R4's fold errors and R5's floor-widening range, both quoted from commit
messages. Both are corrected in place, both corrections are annotated rather than erased, and every
headline number now has a generator that the build runs.

---

## R2's task has the same degeneracy, and its head-selection criterion is defined *by* it

[R13](R13_task_audit/) audited the room task and found it fixed-position. **That lesson had never
been transferred to R2**, whose sequences are `core + core` with `len(core) = T = 64` **constant on
all 24 sequences**.

```
at position T+i the correct next token is core[i+1], at absolute position i+1
distance back = (T+i) − (i+1) + 1 = T

THE ANSWER IS ALWAYS EXACTLY 64 POSITIONS BACK
```

The ids are uniform random over a `39000`-wide range, so there is **no lexical shortcut** — but
there is a **positional** one. **A head attending at a constant distance solves the task perfectly
with no content matching**, and the task cannot distinguish that from prefix-matching, because the
two agree on every sequence it contains.

> **And the selection criterion is the same quantity.** `induction_scores` scores attention from
> position `i` to position `i−T+1` — a **fixed offset** — and its own docstring calls that a
> *"prefix-matching score"*. **The name asserts content matching; the computation measures
> distance.** A label carried where a derivation was needed, inside the function that chooses which
> heads the round is about.

**What this does not break:** every comparison between the top-`k` heads and random-`k` heads. They
face the same task, so R2's floor, its `4` of `5` clearing count and its effect sizes are unaffected.

**What it breaks:** calling them *prefix-matching* or *induction* heads as a claim about **content**.
On this task that is not established. **The repair is the same shape as [R14](R14_position_vs_binding/)'s
— vary `T` per sequence**, so a constant-distance head fails and a content-matching head does not.
It is not run here; the GPU is occupied.

## Why R1 and R2 disagreed — one scale, and the gap is an order of magnitude

Every lesson of the last twenty rounds was applied to R1's task and **none to R2's**. The one that
flipped R1's headline count transfers for free: **is R2's null centred at zero?**

**It is not, on any of the five, and all in the same direction.** The null mean is negative
everywhere, `−0.19` to `−0.63` standard deviations — much further off-centre than R1's band at
`+0.20`, and in the opposite sense: **ablating random heads *hurts* induction logprob, while on the
room task it *helped* the margin.** `d_top` is negative too, so centring **shrinks** the distance and
makes clearing *harder*.

**The count survives anyway — `4` of `5` either way** — because the effects are `6.5×` to `18.7×`
the floor and the correction moves them by hundredths.

```
R1's eight, centred exhaustive floor    1.06  0.37  0.18  0.17  0.07  0.02  0.02  0.01
R2's four valid cells                   1.20  6.50 14.79 18.68
```

> **The two distributions barely touch.** `R1` max `1.06`; `R2` min `1.20`. The rounds do not
> disagree about *method* — they disagree about *effect size*, by an order of magnitude. That is
> what [R5](R5_factorial/)'s `MIXED` over readout, site and mechanism size was circling, and what
> the dynamic-range rescaling below approached from the other side.

`phi-3.5-mini` is the exception in both: `0.12` here, and refused outright in
[R10](R10_exhaustive/) for a readout that scores two of four answers on word fragments.

## Why R1 and R2 disagreed — and it is none of the three factors R5 was built to test

R1 found 7 of 8 effects inside their sampled floor (8 of 8 against the exhaustive one). R2 found
0 of 4. Same operation, opposite conclusions.
[R5](R5_factorial/) spent a 2×2 on *readout*, *site* and *mechanism size* and returned `MIXED`.

Put both rounds on one scale — each readout's **dynamic range**, from the baseline to where the
model sits with the mechanism gone (margin → 0; induction logprob → uniform chance over the ~39k
sampled ids) — and match them at k=5, since R2 ablates the top-5 induction heads:

```
round / model                  range   effect%    2sd%   eff/noise
R1 qwen2.5-1.5b COPY set       4.477    31.9%    21.9%      1.45
R1 qwen2.5-1.5b READ set       4.477     2.0%    21.9%      0.09
R1 internlm2 / phi / qwen3b        —        —   18.9 / 8.2 / 12.7%
R2 llama-3.1-8b               10.118    12.1%     1.8%      6.76
R2 phi-3.5-mini                9.967    10.6%    50.0%      0.21
R2 qwen2.5-1.5b               10.362    45.6%     2.4%     18.86
R2 qwen2.5-3b                 10.378     8.3%     0.5%     15.10
```

**The effects are comparable across both tasks — 2–46% of range. The floors span 0.5% to 50%, a
91× spread.** These two rounds do not differ in signal. They differ in how noisy single-component
ablation is on that task, model and readout.

> **Decomposing `log(effect/floor)` into its two terms: across these six cells the floor carries
> `72.1%` of the variance (`3.1717` vs `1.2298`).** Six cells sharing only `5` distinct floor
> values, so it is a description of this pair of rounds, not an estimate of anything.
>
> ### RETRACTED 2026-07-28 — the held-out half of this claim cannot be recomputed
>
> This paragraph used to continue: *"On R5's six margin cells, which were never used to build this,
> it carries **52%** — a coin flip, with effects spanning 3.8× and floors 5.2×."* **No pairing of
> R5's checked-in fields reproduces any of those three numbers.** `make headline` now sweeps every
> admissible one — `{margin, kl}` × `{final, all, change, stacked}` × `{2sd_final, 2sd_all,
> w_final, w_all}` — and reports the result: `28` pairings spanning `4.3%` to `90.8%`, with `0`
> landing within `3` percentage points of `52`.
>
> The estimator was a free parameter, which is the **third** time in this project after
> [R4](R4_predictability/) and [R5](R5_factorial/): the prose fixed the *claim* and left the
> *computation* unspecified, so the number could not be checked and now cannot be found. A span of
> `4.3%`–`90.8%` also means the choice **is** the result. It is removed rather than caveated,
> because a caveat on an unreproducible number still leaves the number on the page.
>
> **The in-sample half above survives and is now generated.** What died with the held-out half is
> the scope sentence it licensed — *"across tasks the floor dominates; within one task the two vary
> comparably"*. There is no held-out evidence for the second clause.

**And `phi-3.5-mini` is the control that makes this internal.** Same task, same mechanism, same
readout as the other three R2 cells — its effect is a perfectly ordinary 10.6% of range, and it is
**unreadable** (`eff/noise` 0.21) purely because its floor is 50%. That floor is driven by one draw
of thirty at −13.66, which is why R2 reports percentiles rather than a standard deviation.

*Not claimed:* that the floor for induction logprob is exactly uniform chance. It is where a model
with no induction sits given uniformly drawn tokens, and it is an assumption, stated. The k=5
matching is exact; the "no mechanism" endpoint is not.

