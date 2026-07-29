<!-- unbacked-ok: 2.62 24 41.3 41.26 38 16 3.11 3.14 27.58 17.2 35 -- the fresh-clone verification's wall
 time and peak memory, at two dates. 2.62 s / 24 MB was measured 2026-07-28 before the
 randomization tests existed; 41.26 s / 38 MB is the same handle after them, a 16x growth
 (D106). A runtime cannot be emitted by the thing being timed without circularity, so these
 are dated measurements rather than regenerable values. Also: the detector's own
 false-pass rate, plus the earlier rate and the ceiling.
 2605.24059 2606.05378 2605.29126 2605.00333 2607.01002 2604.01094
 2603.11793 2606.09607 2607.04167 2607.18921 2407.08734 2309.16042 2510.00845 2404.15255
 -- arXiv identifiers, not measurements: they name the
 papers that refuted this project's novelty premise and no generator here could emit them.
 57.5 18.1 80.5 1.4 -- results QUOTED FROM 2606.05378 section 6, which this repository did not run.
 29.0 -- 9/31, arithmetic on two counts already shown in the same sentence.
 52.0 3.8 5.2 -- the RETRACTED held-out numbers, kept verbatim so the retraction below can be read
 against what it retracts. They are unbacked BECAUSE they are unreproducible; that is the finding.
 1.089e-07 1.275e-07 8.447e-08 2.398e-02 0.11901 0.11502 -- R21's P7 attack harness output.
 attacks/plant_missing_component.py loads a MODEL, so it is outside the dependency-free
 reference set by design; same exemption class as hook_identity. The script is checked in and
 its command is in its docstring, so anyone with the weights can reproduce these. -->
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
> > **⚠ `D125` — that sentence quotes the WRONG STATISTIC, its median cell is sign-inverted, and an
> > independent adversarial reviewer found all of it.** Three separate breaks, each verified against
> > `R6_intervention/results/r6_intervention_*.json`:
> >
> > **① `rr` is not effect recovery.** `rr = (|pc| / band_sd)_arm ÷ (|pc| / band_sd)_zero` — a ratio
> > of *signal-to-noise ratios*, carrying the factor `band_sd_zero / band_sd_arm`. The prose says
> > *"recovers X% of what zeroing does"*, which is `|pc_arm| / |pc_zero|`. Both are emitted now:
> >
> > ```
> > model            rr_mean   recovery_mean   sign_ok  informative  round_valid
> > internlm2-1.8b    0.4400        0.0562        yes        no          yes
> > phi-3.5-mini      0.2319        0.1199        yes       yes           no
> > qwen2.5-1.5b      0.4398        0.1519        yes       yes           no
> > qwen2.5-3b        0.2368        0.0190         NO       yes          yes
> > ```
> >
> > **② The median cell is sign-inverted.** `qwen2.5-3b`'s zero-arm control is `+1.60537` while its
> > mean and resample arms are **negative**. `R8` defines admissibility as *"arms whose positive
> > control agrees in sign with zero"* and `R7` applies it; **`R6` never did**, and
> > `pc_clears_own_floor` is `|PC| > sd`, magnitude only, so an inverted control passes it. That cell
> > sets the published median at `0.2368` → *"0.24"*.
> >
> > **③ The intersection is empty.** `informative ∧ round_valid ∧ sign_consistent` = **`0` of `4`
> > cells**. The page disclosed *"3 informative cells, 2 of 4 rounds fully valid"* and never that no
> > cell satisfies all three.
> >
> > **The corrected reading, and it makes the limitation WORSE, not better.** On the two cells that
> > are both informative and sign-consistent, median effect recovery is `0.1359` (mean arm) and
> > `0.1516` (resample). **So roughly `85%` of the zeroing effect is not the head's contribution, not
> > `76%`** — the off-manifold problem was *understated* by the number that was published to state
> > it. `n = 2`, and under the strict three-way rule `n = 0`.
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
> **The confirmatory experiment this repository points at HAS NOW RUN.** It is
> [`R19`](R19_crossed_position_support/), a crossed *position × intervention-support* exhaustive
> scan, pre-registered with six amendments and landed 2026-07-28 **at the eleventh attempt**. Every
> statement outside it is still about a **final-query head-output knockout**, written
> `I_final(L,h)`, not about "a head".
>
> **`H-support` is FALSE, confirmatorily, on all four components and all three metrics.**
> Spearman `final × all` is `0.6778` against a required `0.9`; `top-10` overlap `4` of `10`. So
> *"a head"* and *"a head's write at the final query position"* are different objects — which was
> the exploratory finding of [R18](R18_all_positions/) and is now a confirmatory one, on a task
> built independently of the eight.
>
> **`H-published` is NOT enriched** in either scope on any of the three metrics.
> **`H-position` returns `FALSE` by `0.0263`** — and `ADVERSARY.md`'s `A16`, written before the
> data, predicted exactly that the design could not resolve it. **`H-depth` is `UNTESTED`** by
> pre-registration: two models is `n = 2`.
>
> **And the head I bet on lost.** `L17H0` was staked on the top `10` of `168`; it came `37th`.
> Full verdicts: [`R19_crossed_position_support/README.md`](R19_crossed_position_support/README.md).

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

### The obvious remedy — divide by the task's margin — does not work either

If the floor were a fixed fraction of the readout's dynamic range, reporting everything as
`floor / baseline_margin` would make it portable. **R19 supplies a second task with its own margin,
so this is now testable.**

```
task                  margin    floor_final   floor_all    floor/margin final    all
R10/R18 room task     4.4768      0.4870        0.9766          0.1088         0.2181
R19 crossed task      1.6357      0.3099        0.5780          0.1895         0.3533

margin shrinks to  0.3654x        floor shrinks only to  0.6364x (final)  0.5918x (all)
normalisation residual                   1.7417 (final)          1.6198 (all)
```

**⚠ THOSE TWO RESIDUALS ARE WRONG AND ARE KEPT ONLY BECAUSE THEY WERE PUBLISHED.** An adversarial
reviewer found that the two ratios do not share a denominator definition, and checking it at the
object found they do not share a **numerator** definition either. `R10_exhaustive/run.py:273` drops
any item whose unablated argmax over the four rooms is wrong, so **both** of task A's terms are
baseline-correct-only. `R19_crossed_position_support/run.py:356` deliberately does **not** filter —
citing R15's finding that filtering selects on position — so **both** of task B's terms cover all
`1024` items, including the `265` whose margin is negative by construction.

Recomputed under R10's rule by `R19_crossed_position_support/tools/matched_denominator.py`, on the
frozen scan plus one re-run of the baseline pass:

```
                                     margin_B   floor_final_B  floor_all_B   residual final   all
published    (neither term matched)    1.6357       0.3099        0.5780         1.7417     1.6198
denominator only                       2.7220       0.3099        0.5780         1.0466     0.9734
BOTH terms matched                     2.7220       0.4171        0.8063         1.4084     1.3580
```

> **The half-fix is farther from the truth than the original error.** Matching only the denominator
> — the repair the reviewer's finding literally asks for — puts the `all` scope at `0.9734`, below
> `1`, which would have retracted a claim the fully-matched number supports at `1.3580`. **A
> two-term mismatch corrected in one term is not a partial improvement; in one scope it moved the
> answer past the truth and out the other side.**

> **The claim survives at a smaller size.** The floor is `1.36`–`1.41×` wider relative to the
> dynamic range on the harder task, not `1.62`–`1.74×`; about `20%` of the published excess was an
> artefact of my own definitional mismatch. It still misses in the **same direction in both scopes**
> — and that internal replication is *false* under the half-fix, so it is a property of the matched
> comparison, not of the original one.
>
> **The restriction is not a sampling artefact, and this was registered before it was run.** Keeping
> only the `315` of `512` cells whose both replicates are baseline-correct makes every per-head mean
> noisier, and `2 sd` across heads of a noisier quantity is wider by default. Against a
> matched-count random drop (`2000` draws) the observed floor sits at percentile `1.0000` in both
> scopes: `0.4171` against `0.3110 [0.2985, 0.3240]`, and `0.8063` against `0.5783 [0.5532,
> 0.6045]`. **Conditioning on baseline correctness widens the reference distribution by about a
> third, within one task, one model and one metric.**
>
> **Position composition explains part of it and not most of it (post hoc, unregistered).** The kept
> cells are position-skewed — `[64, 61, 42, 28, 23, 24, 29, 44]` of `64` — which is R15's finding
> restated. A null holding those per-position counts fixed and drawing at random within each
> position reaches `0.3404 [0.3285, 0.3523]` (final) and `0.6552 [0.6345, 0.6754]` (all), still far
> below the observed `0.4171` / `0.8063`. So of the rise: cell count is negligible, position
> composition is a part, and the remainder is the correctness selection itself.
>
> **⚠ Two boundaries, and they are large. (1) POST HOC** — the numbers were seen before the question
> was asked, so this carries no verdict word and no threshold. **(2) A BUNDLE change, not a transport
> row** — R19's task differs from R10's in line count, prompt structure, item count **and** the
> presence of a baseline-correct filter, while the table above changes exactly **one** factor per row
> by design. That is why it is kept out of that table.
>
> **Registered forward prediction, before any third task exists:** on a task harder still than R19's,
> `floor / margin` in the `final` scope will exceed R19's `0.1895`. If it does not, the direction
> found here was an artefact of the bundle.

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

### But the ranking does not fully survive either — the headline's own rival, measured

If a local **scale** were the *only* thing that changed, the reference distribution would be a scalar
property in the wrong units, and this repository's framing would be an over-claim. That rival has a
name — **scalar-up-to-scale** — and it was registered with its kill threshold in
[`SHAPE_RANK_PREREGISTRATION.md`](R11_instrument_noise/SHAPE_RANK_PREREGISTRATION.md), **committed
alone, before the code that computes the statistic existed.**

```
qwen2.5-1.5b, band L14-27, four frozen conditions on one 168-head index

  positive controls   synthetic rank-1 0.9891      four independent noise columns 0.3013
  lambda1 / K         0.8477                       permutation null 97.5th 0.3270
  reliability ceiling corr(final/itemsA, final/itemsB)                    0.9942
  intervention        corr(final/itemsB, all/itemsA)                      0.7715
  task                corr(final/itemsB, final/shuffled)                  0.8123
```

> **The two intervention supports share `0.5951` of the per-head variation and do not share `0.4049`** —
> against a measured reliability ceiling of `0.9942`, so **item noise cannot be the explanation.**
> Scale moves `2.0051×`; shape moves too, and by more than measurement error allows.
>
> **Verdict: `UNVERIFIED`, by the rule as written.** `0.7737` disattenuated is below the registered
> `0.90` and above the null, and the `all`-scope reliability `r_yy` has never been measured — so the
> rival is **not** killed. What the test does instead is **pin it to one number**: scalar-up-to-scale
> survives only if `r_yy` lands in `[0.5986, 0.7390]`, i.e. only if the all-position measurement is
> dramatically noisier than the final-query one (`0.9942`) despite carrying twice the spread.
> **[`R19`](R19_crossed_position_support/) measures `r_yy` directly by splitting its `64` base
> instances in half — registered before that data exists.**
>
> Across all `336` heads rather than the band, the same pair falls to `0.5061` and `lambda1/K` to
> `0.7381`. **The degree of conditionality is itself conditional**, which is the finding this section
> exists to state and the reason no single number belongs on the front page.

### One of the five components now has a number: the instrument is `0.0194` of the floor

The status block above says the reference distribution mixes at least five things. **Four of them
have never been given a number, and the fifth had one that this repository withdrew** — *"at most
`0.66%` of the floor's variance can be item sampling"*, killed for extrapolating a quiet layer's
spread to the band. It was never recomputed. R11 stores per-head `sem`, so it can be:

```
var(measured effect over heads) = var(true effect) + mean(sem^2)

  item-sampling share of the band floor's variance   0.0194   95% CI [0.0064, 0.0413]
  all 336 heads rather than the band                 0.0188
  mean sem 0.0169    band sd 0.2446    min sem 0.0013 (the instrument is not blind)
```

> **At `n = 120` items the band floor is dominated by true between-head heterogeneity, not by the
> instrument.** The withdrawn `0.66%` is reported and **not** vindicated — it was low by about
> threefold and sits at the very bottom of the corrected CI.
>
> **And this is a statement about `n`, not about the model.** `sem^2` scales as `1/n`, so item
> sampling would reach `25%` of the floor only at `n = 9.3` items and `5%` at `n = 46.6` (`D6` — it
> assumes nothing else changes with `n`). Every number here uses `n = 120`.
>
> **The retraction that killed the old figure was right, and its argument was not.** It cited
> `+0.962` between a layer's mean `|drop|` and its *between-head spread*; against the actual error
> term the correlation is `+0.5975` over `336` heads. The dependence is also strongly **sublinear** —
> from the quietest layer to the loudest, effect rises `0.0080` → `0.2399` while `sem` rises only
> `0.0051` → `0.0134`. **That sublinearity is exactly why the quiet-layer extrapolation ran low**, and
> neither the claim nor its retraction had seen it.

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

### `I_final` is mostly **not** the head — the rest of the network's response is `3.3x` larger and its sign is a coin flip

For a full session this repository's open sentence was *"what remains is not a property of the head —
it is a property of what the rest of the network does when the head is gone. **That is
compensation**, and the experiment is co-ablation."* **Co-ablation asks whether two heads compose. It
does not measure repair.** The decomposition does, and it needs **no ablation runs at all** —
[`R20`](R20_direct_indirect/), `120` clean forward passes against the `40,320` R10 spent:

```
total(h)     the measured I_final drop            READ from R10's frozen result, never recomputed
direct(h)    delete h's write from the FINAL residual, nothing else recomputed
indirect(h)  total - direct                       the rest of the network's response
```

**The positive control is exact and it is what makes this readable.** Once the last block's own MLP
is re-run and R10's own comparator convention is used, the decomposition reproduces R10's *measured*
ablation on all `12` last-layer heads to `4.069010416662966e-06`. **The direct-path arithmetic is
right, proved on the case where it must be.** Getting there cost three failures, all mine, and they
are in [the amendment](R20_direct_indirect/PREREGISTRATION.md) — the registered control's premise was
false (every attention block is followed by *its own* MLP), then my capture hook fired on my own
re-invocation and corrupted its cache, then my comparator differed from R10's.

```
|total| > |direct|                        115 of 168      sign-test p 0.000001953788031425443
sign(total) == sign(direct)                79 of 168      p 0.4876   -- a coin flip
median |total| 0.0663   median |direct| 0.0199            ratio 3.3251x
pooled Spearman(|total|, |direct|)                        +0.0166
within-layer partial(|centred total|, |direct| | mean_norm)   +0.2265   p 0.0078
```

> ### ⚠ **RETRACTED, `D151`–`D156`. An independent adversarial reviewer moved five of the six claims above down a bucket, and I reproduced every one of its recomputations to the digit.**
>
> **① The `p = 2e-06` was manufactured by the heads the pre-registration itself excludes.** `46` of
> the `168` have `|direct| < 0.01` — *"`direct ~ 0` **by construction**"*, its own words — and they
> were dropped from the ratio and **kept in the sign test**. Split it:
>
> ```
> ALL 168            |total| > |direct|  115/168   p 0.00000195378803142544   <- published
> usable 122          71/122   p 0.0849806                                    <- not significant
> excluded 46         44/ 46   p 0.0000000000307523                           <- the entire signal
> ```
>
> A test of `|total| > |direct|` on heads whose `|direct|` is definitionally zero is a test that
> `|total| > 0`. **`"World R is dead at p = 2e-06"` is withdrawn.** On the registered usable
> population the sign test says nothing (`p = 0.085`).
>
> **② The registered depth separator was computed on the wrong population and points the other
> way.** The pre-registration calls it *"a second, independent separator … under World R the ratio
> must depend on depth; under World N it must not"*. `analyze.py` iterated all `28` layers, folding
> in `14` layers outside the registered band. On the band it is **`+0.5297` over `14` layers**, not
> the published `-0.1314`. **The separator registered to discriminate R from N shows depth
> dependence, and it never reached this page.**
>
> **③ The `+0.2265` partial is dead.** `indirect = total - direct` **by construction**, so `|direct|`
> is a component of `|total|` and the null that shuffles `|centred total|` while holding `|direct|`
> fixed destroys the identity. Against a null that preserves it — permute `indirect` within layer,
> re-form `total = direct + indirect_perm`, same seed, same `20000` draws:
>
> ```
> published null (shuffle Y)      mean +0.0004   97.5th 0.1655   p 0.0078   m_break 6.37
> shared-term-preserving null     mean +0.1849   97.5th 0.3330   p 0.2884   m_break 0.17
> ```
>
> **And the ranking inverts.** `mean_norm` and readout reach are not components of `total`, so their
> nulls sit at zero; `direct`'s excess over its own null is `+0.042` against readout reach's
> `+0.171`. **`direct` is the WEAKEST of the three predictors, not the second strongest.** The
> pre-registration named this exact confound — *"`indirect = total - direct` shares a term with
> `direct` … that statistic is therefore not used, and naming it here is the point"* — refused it in
> the deflationary direction, and then committed it in the inflating one.
>
> **④ The positive control validates a quantity claims ①–③ never use.** The gate passes on
> `direct_plus_own_mlp_recomp`, which exists for `12` of `336` cells. `direct_renorm` — the quantity
> every claim uses — fails that same control by `18.4783x`. What the control does license: the `W_O`
> slicing, the RMSNorm basis, the tied-embedding readout, the item set. What it does not: that
> `direct_renorm` and `total` are commensurable. **It proves the opposite.**
>
> **⑤ `3.3251x` is wrong twice.** `at[len(at)//2]` on an even `n = 168` is the `85`th order
> statistic, not a median, in a file that defines a correct `median()` and uses it four lines away.
> True median ratio `3.2978`. And the honest per-head figure on the registered usable population is
> **`1.8960x`**, not `3.3x`.
>
> **⑥ The sign-agreement test used the wrong null** — `p = 0.5` requires 50/50 marginals and they
> are `0.595 / 0.399`. Fisher exact on independence gives `0.8726`, not `0.4876`. **The conclusion
> survives and strengthens**; only the test was wrong.
>
> **⑦ The heading over-claimed and is corrected.** *"`I_final` is mostly not the head"* — the total
> effect **is** the head's causal effect by definition. The decomposition splits it **by route, not
> by agent**: a head whose write is read and amplified by a later component is fully responsible for
> that term. What is licensed is the narrower body sentence: *the head's direct linear write to the
> final residual is a minority of the measured drop.*
>
> **⑧ `UNVERIFIED` was spent as an acquittal.** The verdict word was retracted to `UNVERIFIED` and
> then two worlds were declared dead from statistics chosen after seeing the data. Different
> post-hoc statistics were available and they disagree: sign test on the registered usable set says
> nothing (`p = 0.085`); the registered depth separator on its own population points at World R
> (`+0.5297`). **Both worlds go back to live.**
>
> **⑨ Neither of `R20`'s p-values was entered into the multiplicity family** that `A18` opened one
> round earlier, and both sit at or below its kill line: `m_break` `6.37` as published, `0.17`
> under the correct null, `0.59` for the sign test on the registered population.
>
> **What survives the attack:** the direct-path arithmetic itself — the closed-form readout gate plus
> the `4.069010416662966e-06` last-layer reproduction — which the reviewer states it could not break;
> the capture-hook diagnosis; and the git ordering of the pre-registration. **The measurement is
> sound. Almost everything I concluded from it was not.**

### What the indirect term IS: half later attention, a quarter MLPs — and `85%` of the motion cancels

`R20` left a term `3.3x` the head's own contribution with **no account of it**. The last time this
repository had a gap that shape it named a mechanism (*"that is compensation"*) and spent a session
pointing at the wrong experiment. [`R21`](R21_indirect_attribution/) **names none.** It attributes.

The split is an **exact identity**, not an estimate: `rms(res)` is a scalar, so for a fixed
comparator the margin is additive over component writes.

```
class   median share   median |sum|   per member   cancellation   members
ATT         0.4845        0.055965     0.000167       0.1734        335
MLP         0.2341        0.047556     0.001698       0.1392         28
NORM        0.1706        0.030222     0.030222          -            1
EMB         0.0000        0.000000     0.000000          -            1

OWN+ATT+MLP+EMB+NORM reproduces this round's own measured drop to  1.7878479721677998e-07
last-layer heads: ATT is exactly 0, and 0 from any later layer      structural control, exact
OWN vs R20's independently measured `direct`:  Spearman +0.9068
```

> ### ⚠ **RETRACTED, `D159`–`D167`. An independent reviewer returned `9` confirmed findings, and the predictions I registered before dispatching it caught `5`.**
>
> **① There are ZERO non-tautological controls left in this round.** `D157` retracted the first as a
> tautology and the amendment then asserted the other two *"were always the real ones and both are
> non-trivial"*. Both are forced too. Last-layer `ATT = 0` is causality, proved from this round's own
> data — `att_abs`, a sum of **absolute** values, is exactly `0.0` on all `12` heads, so every element
> was exactly zero on all `120` items. And `OWN` is not validated against anything independent:
> `Spearman(OWN, R20 direct_linear) = 0.9998810493974013` — **`OWN` *is* `direct_linear`**, so the
> control measures `R20` against itself, and the `0.0068` by which it clears its registered `0.90` is
> **smaller than `R20`'s own internal convention gap**. *"Nothing in the round checks the `OWN`/`ATT`
> boundary or the `ATT`-vs-`MLP` class assignment — the two partitions the entire result consists
> of."*
>
> **② Both per-member counts include components that cannot contribute.** Ablating at layer `L`
> cannot move any attention head at layer `<= L` or any MLP at layer `< L`; live members are
> `(27-L)*12` and `28-L`, medians `78` and `7.5`. **`ATT` per-member is wrong by `7.5x`, `MLP` by
> `3.7x`, and *"`10x` more per member"* is `4.97x`.** That figure is the round's own **registered
> confound control** — the number it exists to produce is the one that is wrong.
>
> **③ The `44`-head rescue subgroup selects the low-signal heads.** `Spearman(flip_rate, |own|) =
> +0.5762`, Mann-Whitney `p = 6.1322e-08`, `3.2x` smaller `|own|` — the same near-zero population that
> manufactured `R20`'s `p = 2e-06`. Against a **depth-matched** null its `0.5294` sits at the `20`th
> percentile while `0.90265` of random same-depth draws reach `>= 0.50`. **Less attention-dominated
> than chance. Withdrawn, not merely un-promoted.**
>
> **④ `85%` cancellation is at or below its own null.** The factor pools within-class cancellation
> with **across-item sign flipping** — proved by a **one-member** class at `L27` reporting `0.672`,
> where there is nothing to cancel against. Against `1/sqrt(n_live)`, `ATT` cancels *less* than
> independent random signs at `11` of `13` layers. The sentence *"a small net residue of a large
> amount of motion"* carries no information for `ATT`.
>
> **⑤ `NORM` is undersized about `2x` and mis-signed.** Its share's denominator is `SUM|class|`, not
> the indirect term. Against the indirect term it is `0.3033`, and `0.4279` of the whole drop; it
> exceeds the entire indirect term on `39` of `168` heads and is the largest class on `21`. Its median
> **signed** share is **`-0.0625`** — the gain typically *opposes* the drop, and the absolute-value
> convention turned opposition into *"carrying 17% of it"*. **World NORM is not dead.**
>
> **⑥ The shares do not sum to `1`** (`0.8892`), and two aggregations that do move `MLP` by `+30%` to
> `+52%`. **⑦ `3.8417x` mixes the two comparator conventions Amendment 1 calls incommensurable**
> (same-convention `4.1502x`; on the usable population `2.0052x`) **and its `(R20 reported 3.3251x)`
> anchor is retracted** — it should read `1.8960x`. **⑧ The class share is largely a count of
> downstream components**: redrawing the band as `L14`–`L21` gives `ATT ~0.62` and flips the verdict
> to `ATTENTION-DOMINATED`, and no depth control is reported.
>
> **What survived:** the additivity algebra, the `W_O` column-block decomposition, the MLP capture
> point, `EMB` as a genuine control against *omission*, the item set — and **the registered verdict
> `MIXED`, which held under every reaggregation the reviewer tried.**
>
> **The calibration score, registered before dispatch**
> ([`ADVERSARY_PREDICTIONS.md`](R21_indirect_attribution/ADVERSARY_PREDICTIONS.md)): recall
> `5/9`, precision `5/8 = 0.6250` → **`CALIBRATED`**. And the rule flatters me: **recall
> counts findings, it does not weigh them.** The two largest numeric corrections — the live-member
> counts and `NORM`'s denominator — are both ones I did not predict, and the sentence I registered
> under *"what I expect to be WRONG about"* named `0.001698` as the number I had inspected least.
> **It is wrong by `3.7x`.**

### The repository's own family of decision rules — and a correction would make its headline *stronger*

`ADVERSARY.md`'s `A18` was confirmed by two reviewers and left standing: `31` registered decision
rules, `alpha = 0.05` throughout, no correction anywhere. `D145` made it `33`. **The obvious repair
is the one that must not be applied blind**, and this is the reason:

> A correction lowers `alpha`. That makes a **presence** rule (`fires when p <= alpha`) harder — and
> an **absence** rule **easier**. `R19`'s `H-position` is registered literally as `p_pos >= ALPHA`:
> **failing to reject is a PASS condition.** So does *"the eight are not enriched"*, at `p = 0.8069`.
> **A blanket Bonferroni across these rules would strengthen this repository's central claims
> without a single new observation.**

So the family is split by direction before it is corrected (`detectors/multiplicity.py`, registered
in [`MULTIPLICITY_PREREGISTRATION.md`](MULTIPLICITY_PREREGISTRATION.md)). The inventory is derived by
walking the emitter, not hand-listed; `58` p-values, `14` presence, `21` absence, `10` resolution
statements, `3` controls, `4` retracted, `4` diagnostic, `2` **not p-values at all**, `0` unclassified.

> **`D158` — the walk's name rule is not the concept, and its own `UNCLASSIFIED` bin caught it.**
> `p_total_positive` and `p_direct_positive` are **marginal proportions** from a `2x2` sign
> table. They begin with `p_`, so the inventory would have folded them into a multiple-testing
> family as if they were tail probabilities — the repository's own overshoot #2, *a lexicon whose
> match rule is not the concept*, **inside the instrument built to audit families.** Found only
> because the pre-registration required `UNCLASSIFIED` to be printed rather than dropped.
>
> The same pass classified `4` **retracted** rules (`D151`, `D152`, `D155`) and `4`
> **diagnostics** — the corrected numbers that replaced them. A retracted rule left in the family
> would make the correction look harsher than it is; one deleted from the inventory would hide
> that it was ever counted. Both are wrong, so it carries its own class.

The statistic is family-size-free, because the family size is bookkeeping — `12`? `31`? `33`? —

```
m_break = floor(alpha / p)     the largest family in which Bonferroni still rejects
ceiling = alpha * (N + 1)      what m_break CANNOT exceed for a null of N draws, whatever the effect
```

```
presence rule                                  p        m_break   ceiling   at its null's floor?
condition_shape_rank  p_lambda1 (x2)  0.0000499975         1000      1000    yes
ov_permutation_null   6 model x category    0.0005          100       100    yes
selection_overlap     mean-of-ratios     0.0097998            5      2500    no
selection_overlap     L22H7 one head     0.0118343            4      2500    no
selection_overlap     sum-ratio          0.0149797            3      2500    no
set_enrichment        L17H0 one head     0.0295858            1      2500    no
mechanism             alignment partial  0.0454977            1         -    no
selection_overlap     median-of-ratios   0.2768545            0      2500    no   (does not fire)
```

> ### **`MULTIPLICITY-BITES`, and the shape of it is worse than the count.**
>
> **`5` of the `13` firing presence verdicts die below a family of `6`.** And of the `8` that
> survive a family of `14`, **`8` are pinned at their own null's resolution floor** — their `p` is
> the smallest the instrument can return, so `m_break` measures **how many draws were bought**, not
> how large the effect is. **Not one presence verdict with a graded `p` survives.**
>
> **The absence family is untouched, and that is the finding I was most afraid of and did not get.**
> Every absence `p` is `>= 0.0704`, so **no correction at any family size can create or destroy
> one** — the requested repair could not have manufactured a claim. The repository's *headline*,
> which is a set of nulls, is multiplicity-immune; its *positive side-claims* are not.
>
> **What this does not license:** deleting the five. `m_break` is Bonferroni, the most conservative
> of the corrections, so it is a **lower** bound on robustness; Holm and BH are kinder. And the
> selection-overlap trio survives its **own** family of three. The honest statement is a scope, not
> a retraction: *these hold if the tests you count are the ones in their own round.*

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

### Replicated on a second model — and the null is *flatter* there

Every instrument comparison above is `qwen2.5-1.5b`. The `OV` circuit costs nothing to compute on a
second model, and `R10`/`R18` already hold that model's ablations.

```
qwen2.5-3b, band L18-35, 288 heads, scaled basis

set        n   perfect-wins    max dominance          final RMSNorm g spans 232x
rooms      4        45             3.067              (against 2063x on 1.5b)
objects    8        23             4.617
persons    8        15             3.509

edge                            pooled     within-layer
OV.rooms   x ablation.I_final   +0.0335       -0.0056
OV.rooms   x ablation.I_all     +0.0379       -0.0359
OV.objects x ablation.I_final   +0.0140       +0.0092
OV.objects x ablation.I_all     +0.0452       -0.0301
OV.persons x ablation.I_final   +0.0416       +0.0649
OV.persons x ablation.I_all     +0.0658       +0.0093
```

**All six edges sit within `±0.07`** — on `1.5b` they ran `−0.14` to `+0.22`, so **the second model is
*closer* to zero, not further.** And the positive control is *stronger*: `45` heads copy all four
rooms against `25` on `1.5b`. **The instrument finds plenty of copiers; they are simply not the heads
ablation flags.**

> **Scope, and it is narrower than "two models" sounds.** Both are `Qwen2.5`, same family, same
> training data, same architecture — **not independent draws.** And the **attention** edges cannot be
> replicated at all, because `E132`'s attention scores exist only for `1.5b`. **What replicates is the
> `OV × ablation` null; the `attention` edges remain `n=1`.**

### The band boundary is arbitrary — the count survives it, the floor does not

Every number in this repository is conditioned on `L14`–`27`, and the sham is `L0`–`7`. **Those are
not complementary: `L8`–`13`, seventy-two heads, is in neither region and is silently excluded from
every contrast.** And `L14` was never chosen — it is "the upper half of `28`".

```
per-layer sd of raw drops     L12 0.0891   L13 0.0913   L14 0.0882   L15 0.2231
```

**The jump is `L14 → L15`, not `L13 → L14`.** Ranking all `25` possible boundaries by the ratio of
mean `sd` above to below, **`L14` comes `11th`. The best cut is `L8`** — which is exactly where the
*sham* band ends. **The sham boundary is well placed and the band boundary is not.**

```
region                        n      mu      floor   clear   published clearing   the eight's ranks
BAND L14-27                 168   +0.0479   0.4870    10          1/8         10 41 77 79 129 157 158 162
L15-27  (drop L14)          156   +0.0495   0.5032    10          1/8         10 40 75 76 123 144 145 149
L8-27   (include middle)    240   +0.0347   0.4179    11          1/8         10 50 78 110 200 229 233 236
ALL 28 layers               336   +0.0259   0.3565    14          1/8         10 55 75 129 276 290 293 295
SHAM L0-7                    96   +0.0040   0.0792     4           -
L8-13   (discarded middle)   72   +0.0038   0.1560     6           -
```

**`1 of 8` clears in every one of the four windows.** The headline count is invariant to a choice that
was never justified — that is a real robustness and it is stated as such.

> **What is *not* invariant.** The floor runs `0.3565` to `0.5032` — **`1.41×` from the window alone,
> at fixed model, task, intervention and `k`.** That is a **fifth axis** for the transport result
> above, and the widest one available without changing anything about the experiment.
>
> **And the eight's ranks move materially even after normalising for `n`.** The fraction of the
> reference class ranked *above* the worst published head is `0.9643` in the published band and
> `0.8780` over all `28` layers. **That is not a percentile** — rank `162` of `168` is the `3.6`th
> percentile by magnitude, and calling the fraction a percentile inverts the direction.
>
> **The discarded middle is the transition.** `L8`–`13`'s floor is `0.1560`: twice the sham's and a
> third of the band's. **Excluding it was not neutral — it removed the only region that could have
> shown where one regime becomes the other.**

### That window row was `n`-confounded as written — the control it needed, run after the fact

`arm_contrast`, this repository's own detector, asks whether a control arm differs from the studied
arm **only** in the property it claims to isolate. **The `L14-27` versus all-`28` row changes the
window *and* the sample size**, `168` against `336`, and a `2σ` estimate's own sampling error depends
on `n`. I wrote that row without checking.

**The control holds `n` fixed and destroys only the window structure:** resample `168` heads at random
from all `336`.

```
observed   L14-27 floor 0.4870        all-28 floor 0.3565        ratio 1.366x

null, 20,000 random 168-head draws
  median 0.3566    2.5th 0.2648    97.5th 0.4294    MAX 0.4639
  observed 0.4870  ->  never reached in 20,000 draws
```

**The window effect is real.** It is not the sample size.

**And the mirror is sharper than the original contrast.** The sham window's floor is `0.0792` on `96`
heads, while a random `96` of `336` gives a median of `0.3530` — **`4.4576×` below.** So *each* window is
individually extreme against a size-matched random control, in opposite directions. **That is a
better statement of the layer effect than "band vs sham `6.15×`"**, because a ratio between two
extremes says nothing about which of them moved.

> The one-sided `p` here is at the permutation floor `1/20001` and means **"never reached in
> 20,000 draws"**, not a value resolved to five places — the same floor caveat as the permutation null above.

### ⚠ The "third instrument" is not a contribution — the paper that says so was already in this repository's own prior-art table

`D108` introduced the `OV` circuit as *"a third instrument, independent of both attention and
ablation"*, and `D111` framed the finding as *attention captures where a head reads, not what it
writes.* **Both are the abstract of a paper published `2026-07-01` — and that paper's arXiv id is
cited in [`PAPER.md`](PAPER.md)'s own prior-art table, filed under "random-heads controls."**

> `arXiv 2607.01002`, *Logit-Contribution Scoring Identifies Non-Literal Retrieval Heads*
> (Gema, Alex, Minervini):
>
> *"existing detectors miss these heads by construction: they reward heads whose attended token
> matches the generated token, a literal-copy criterion that captures **where a head reads but not
> what it writes through its output-value (OV) circuit**"*
>
> *"a **write-aware detector that scores each head by the projection of its OV-circuit output onto
> the answer-token unembedding direction**"* — three model families, causal validation by
> mean-ablation, **and a random-heads control.**

**`LOCOS` is the instrument, better formulated and causally validated.** Scoring against the
*answer-token* unembedding with a needle / off-needle contrast is sharper than the diagonal-dominance
statistic used here, and they demonstrate the consequence by ablation rather than by correlation.

**This repository read that paper as *"a paper that uses a random-heads control"* and never as
*"a paper whose contribution is the distinction I would later claim."*** That is the failure mode
named elsewhere in this ledger as *a label is not a description* — committed against a citation
already on the page.

**What is void:** the framing of `D108`/`D110`/`D111` as introducing something. **What is not:** the
measurements themselves. `L22H7` really does rank `140`/`136`/`149` of `168`; the permutation null
really does put those counts beyond `20,000` draws. **Independent re-derivation is not a
contribution, and the numbers are unaffected by learning that.**

**What may still be this repository's:** the *transport* result — that a random-component floor fails
to carry across configurations while carrying perfectly across item samples. **Neither paper does
that. But an abstract-level search cannot settle it**, which is the confound written before this
search ran and the same reason the original novelty premise died. **`UNVERIFIED`, not `novel`.**

### The transport claim is prior art too — three times, and the closest one states the thesis almost verbatim

`D119` left the transport result as the one possibly-novel thing here and marked it `UNVERIFIED`,
because the query that killed the `OV` claim was not aimed at transport. **Aimed properly, it lands.**

| paper | what it already says |
|---|---|
| [`2407.08734`](https://arxiv.org/abs/2407.08734) *Transformer Circuit Faithfulness Metrics are not Robust* (2024-07) | *"existing methods are **highly sensitive to seemingly insignificant changes in the ablation methodology**"*; scores *"reflect **both the methodological choices of researchers as well as the actual components**"*; **"the task a circuit is required to perform depends on the ablation used to test it"** |
| [`2309.16042`](https://arxiv.org/abs/2309.16042) *Towards Best Practices of Activation Patching* (2023-09) | *"**varying these hyperparameters could lead to disparate interpretability results**"* — metrics and corruption methods, systematically |
| [`2510.00845`](https://arxiv.org/abs/2510.00845) *Mechanistic Interpretability as Statistical Estimation* (2025-10) | *"circuit discovery is ... a **statistical estimation problem**"*; *"**the causal effect of a component is a volatile random variable rather than a fixed property**"*; *"small perturbations in input data or hyperparameters yield **vastly different circuits**"* |

**The last of those is this repository's thesis, stated in an abstract, `9` months before it started.**

> **So the project has no established novelty claim.** The floor result, the instrument comparison and
> the transport framing each have published prior art, and in two of three cases the paper was already
> cited here or trivially findable.
>
> **What it still is:** a worked audit of one prior experiment, carried out in public, with an
> unusually complete error record — `174` rows, each naming what was wrong and what the operation on
> it was.
>
> > **⚠ `D123` — this said `120` for two rows, and BOTH of this repository's checkers are blind to
> > it.** An independent reviewer found it, not the gate. `headline.py --check` compares the
> > *emitter* against a hardcoded expectation, never against this sentence;
> > `detectors/prose_numbers.py` compares *prose* against the emitter but **cannot see bare
> > integers**, a blind spot it declares and asserts in its own selftest. **A prose integer is
> > therefore checked by neither.** `120` also collides with the `n = 120` item count used
> > throughout, so even a human eye slides past it. This is the number this file's own
> > [`ADVERSARY.md`](ADVERSARY.md) predicted an adversary would *not* find. **That is a case study, not a contribution to method**, and saying so is the only honest
> version.

**And the search discipline is part of the finding.** The first transport query returned ten papers on
dialogue contradiction, document expansion and pronoun resolution — **zero relevant.** That was
**silence from a badly phrased query, not evidence of absence**, and the tool had returned two
squarely relevant papers minutes earlier. **I have now been wrong in the same direction twice: an
abstract search that finds nothing is not a null, it is an unfit instrument until a working query
proves otherwise.**

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
>
> > **⚠ `D146` — every one of these four `p` values dies in a family of six.**
> > `detectors/multiplicity.py` reports the largest family in which Bonferroni still rejects:
> > `mean-of-ratios` `5`, `L22H7` `4`, `sum-ratio` `3`. Inside its **own** family of three
> > aggregations the pair survives; inside this repository's `14` firing presence rules it does not.
> > **The claim is not withdrawn — it is scoped: it holds if these are the only tests you count.**

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
> > **⚠ `D124` — that positive control is an ARITHMETIC IDENTITY, and an independent adversarial
> > reviewer found it, not any instrument here.** `top8` is by construction the argmax of the test
> > statistic over all `8`-head subsets of the band, and every null draw is an `8`-head subset of the
> > same band, so `T(null) <= T(top8)` with probability `1`. It establishes nothing about power. By
> > this repository's own rule — a null is inadmissible until its instrument passes a positive
> > control — the central negative claim was `UNVERIFIED`.
> >
> > **A real positive control plants an enrichment of known size and measures the detection rate.**
> > Same matched-layer distinct-per-layer test, `300` plantings x `2000` null draws per point:
> >
> > ```
> > planted enrichment   0.00   0.25   0.50   1.00   2.00   4.00   (band sd)
> > detection rate       .0433  .1333  .3533  .8933  1.000  1.000
> > ```
> >
> > **The `delta = 0` row is the calibration gate and it passes: `0.0433` against a nominal `0.05`.**
> > `MDE80 = 0.9136` sd `= 0.2225` in margin units. The eight's observed enrichment is
> > **`-0.1226` sd** — they are *below* the band average, not above it.
> >
> > **So the null is no longer `UNVERIFIED`; it is a BOUNDED ABSENCE.** The correct statement is not
> > *"the eight are not enriched"* but: **a set-level enrichment of `0.9136` sd or more would have
> > been caught at a rate of `0.8933`, and what was observed is `-0.1226` sd.** Enrichments below
> > `0.9136` sd are not excluded by this test and never were.
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
