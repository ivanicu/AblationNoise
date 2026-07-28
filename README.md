<!-- unbacked-ok: 2605.24059 2606.05378 2605.29126 2605.00333 2607.01002 2604.01094
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

Then it points the measurement at its own author's prior results. The finding, stated at the size
the evidence supports:

> ## The heads that ablation flags loudest are not the heads anyone identified — and are mostly heads whose removal *helps*
>
> `L22H7` was independently established as the copy head for this task. Ablate every one of the
> `168` heads in the studied band, once each, and it ranks **`56` of `168`**.
>
> ```
> 9 of 168 heads clear the exhaustive floor of 0.4870 at k=1, up to 2.54×
> 0 of those 9 are among the eight published heads
> 7 of those 9 clear in the HELPING direction — ablating them makes the model MORE correct
>
> the eight published heads rank   10 · 55 · 56 · 109 · 113 · 115 · 116 · 143   of 168
> ```
>
> **Ablation magnitude and mechanistic role are close to unrelated on this task.** The claim is
> about the **ranking**, which needs no threshold — see the correction below for what the *count*
> does and does not establish.

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
> **The count does not change** (leave-one-out, each head judged by a null excluding it: still `9`).
> **The interpretation breaks instead.** My severity estimate was too low, which is the row scoring
> me rather than the other way round.
>
> **What survives is every statement about ORDER**, because a ranking needs no threshold: the eight
> published heads at `10 · 55 · 56 · 109 · 113 · 115 · 116 · 143`, the proven copy head `56`th, and
> `0` of the top nine among them. Whether any individual head is *resolvable* is a question about
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

RESOLVABLE at 2σ      8 of 8            DISTINGUISHABLE from a random head      0 of 8
```

> ## Every one of the eight is measurable. Not one of them is special.
>
> **The measurement was never the problem.** Being *resolvable by the instrument* and being
> *distinguishable from a random component* are different properties, and only the second failed —
> for all eight, including the head independently proven to implement the behaviour.

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
make verify     # 5 selftests + the attack suite, 41 recomputed numbers, 27 markdown files
make headline   # just the numbers, recomputed from the checked-in results
```

**No GPU, no model download, no network, and no dependencies** — `make verify` runs on a stock
Python 3 interpreter with nothing installed, in about two seconds. That is deliberate: a repository
whose subject is *whether you can check a claim* has no business requiring a scientific stack before
you can check its own. (Reproducing a *round* needs `torch` and `transformers`; verifying the
**claims** needs neither, and the two paths are separate targets.)

`make verify` exists because this repository has twice caught **itself** shipping a number that
could not be regenerated — R4's fold errors and R5's floor-widening range, both quoted from commit
messages. Both are corrected in place, both corrections are annotated rather than erased, and every
headline number now has a generator that the build runs.

---

## The rounds

Each round is a folder: its pre-registration, its amendments, its runner, its results.

| | question | verdict |
|---|---|---|
| **[R1](R1_noise_floor/)** | how large is the ablation noise floor? | at k=1, *which* component you ablate produces **2.7–12.3×** more spread in the outcome than *that* you ablated one — a ratio of standard deviations, 4 models, 3 families |
| **[R2](R2_inversion/)** | how often does ablating a *known* mechanism go the wrong way? | **rare** — 0 of 4. The attractive hypothesis died |
| **[R3](R3_withdrawn/)** | is a sibling project's specificity control a single draw? | **withdrawn before spending compute** — its own records refuted the premise |
| **[R4](R4_predictability/)** | can readability be predicted from cheap observables? | across models **UNVERIFIED** — the pre-registered gate is met by 60 of 324 admissible estimators, so its own first verdict was withdrawn. Within a model the floor is a power law and **two measured points fix the curve** (12/12 held-out within 2×) |
| **[R5](R5_factorial/)** | which factor decides readability: site, readout, or mechanism size? | ablating at **every** position instead of one made the effect-to-floor ratio **worse in 6 of 6** model × readout cells |
| **[R6](R6_intervention/)** | is the floor a property of ablation, or of *zeroing*? | **NOT MET** — its own control arm reproduced R1 to **0.0% on 4 of 4 models**, then a pre-registered diagnostic showed the comparison arms move the residual stream 4–7× less, so the design cannot decide. The question stays open |
| **[R7](R7_norm_matched/)** | at a **fixed** perturbation size, does the *direction* change readability? | **NOT MET** on the gate (2 of the 4 cells were droppable). But with displacement matched to **0.00%**, a known effect is **least** readable in the on-distribution direction and **most** readable in the zeroing direction, in **4 of 4** cells — the opposite of what the off-manifold objection predicts |

| **[R8](R8_component/)** | *which component* of a head's output does the intervention destroy? | **NOT MET** — and the round's own prediction matrix had a **mis-derived row**, which collapsed two of its three worlds. One world still died: destroying the item-**constant** component is worth as much as destroying both (`4 of 4`), while destroying only the item-**varying** component is worth far less (`3 of 3`) |
| **[R9](R9_depth_profile/)** | is R1's headline a **depth** artifact? | gate **UNVERIFIED** — its estimator extrapolates the sham half to the band's depth and returns negative or absurd values. The **curve** stands: a model's quietest and noisiest layer differ by **8.1× to 96.2×** (4 of 4 models), so R1's two arms compare pools whose internal spread exceeds the difference between them |
| **[R10](R10_exhaustive/)** | is the floor pooled over the wrong population? | **no — and the sharper test strengthens the headline.** Every head ablated once, zero sampling error: against each effect's **own layer's** floor, **8 of 8** published effects are inside, including the one that cleared the pooled floor |

### R9 is the round that can retract R1, and an outside reader found the hole

R1's statistic is `sd(band draws) / sd(sham draws)`. **The band is the upper half of the stack and
the sham is the early layers.** So two explanations predict the same number — *this band holds a
mechanism, so which head you pick matters*, and *later layers are generically more head-heterogeneous
than earlier ones* — and nothing in R1–R8 separates them. Eight rounds inherited the confound, and
R6's and R7's exact reproductions of R1 reproduced it perfectly along with the number.

[R9](R9_depth_profile/) replaces the ratio with the **whole curve**: 30 single-head draws from each
layer separately, with the band's baseline being the **sham half's own trend extrapolated to the
band's depth** — the comparison R1 should have made. Its `DEPTH-EXPLAINS-IT` branch rewrites the
first sentence of this page in the same commit as the result.

### R6 was the round that could break this repository. It did not — and it did not clear it either.

Every number above came from setting a component's output to **zero**, which hands the downstream
layers an input they never see. If the floor is that off-distribution damage, this work restates
advice the field already publishes. [R6's pre-registration](R6_intervention/PREREGISTRATION.md)
committed, before any result existed, to rewriting the sentence at the top of this page in the same
commit as the result.

**That sentence is not rewritten, and the reason is not that the test passed.** R6 compared `zero`
against `mean` and `resample` — and a pre-registered diagnostic, run before the write-up, found that
at the final position a head's output is **73–86% item-independent** on all four models. The
comparison arms displace the residual stream by only **14–27%** of what zeroing does. Comparing
those floors compares two *magnitudes*, not two *kinds*, so the round **cannot decide** and reports
`NOT MET`. [R6 in full](R6_intervention/).

**[R7](R7_norm_matched/) fixed the size and varied only the direction** — three arms writing a point
exactly `‖x − μ‖` away from `x`, matched to **0.00%**. Its gate also returns `NOT MET`, on a count:
two of four cells were droppable, one for a dead arm and one by R1's own live-sham exclusion.

**And its third arm was retracted.** An outside reader found that `randdir`'s positive control is
**sign-inverted on 4 of 4 models** — its `|PC|/sd` was the magnitude of a control pointing the wrong
way, which is the exact failure [R2](R2_inversion/) was built to hunt. This repository owns a
detector for it, [`control_fitness`](detectors/control_fitness.py), and **no runner had ever called
it**. What survives, counting only cells where both compared arms' controls agree in sign with the
anchor: a known effect is **less readable in the on-distribution direction than in the zeroing
direction, on 3 of 3 admissible cells** — the off-manifold objection predicts the reverse, but this
is now three cells and two arms, not four and three.

What both rounds established on the way: the zero arm reproduced R1's `ratio_k1` to **0.0% on four
models out of four, twice**, through two independently rewritten measurement paths. R1's number is
not an artifact of R1's own code.

## The result that is most useful to someone else

**A floor cannot be looked up.** Changing four English nouns in the answer vocabulary moved it 1.7×
on a fixed model; across models the exponent spans 0.3–0.8 and the scale spans 8.8× on an identical
task. But within a model it is a clean power law in set size (R² 0.935–0.985), so **measuring two set
sizes fixes the whole curve** — two conditions instead of a sweep, **provided the two are widely
separated and one of them is small**: of the ten possible pairs, six score 12/12 and the narrowest
high-k pair scores 6/12. And the honest margin is against a **measured** floor — a trivial
predictor that ignores set size entirely already scores 9/12, while a null that permutes the sd
values across set sizes reaches 12/12 in **0 of 200** draws.

**And ablating harder makes it worse.** When an ablation shows nothing the reflex is to cut more.
Across three models and both readouts, moving from one position to every position made the
effect-to-floor ratio worse in **six of six** cells — and it does so under both candidate floor
definitions (2 sd and the p10–p90 band), which widen by 1.31–3.34× and 1.39–5.46× respectively while
the effect itself changes by 0.69–1.94×.

## The detectors

Each was born from a specific failure in this work, carries its own positive control, and refuses
rather than degrading. A detector that has never fired is not a detector, so each one's `--selftest`
replays the real incident that produced it.

| | asks | born from |
|---|---|---|
| [`readout_tokens`](detectors/readout_tokens.py) | does your readout distinguish the answers you are scoring? | a run reported `n=0` because a SentencePiece tokenizer gave all four answers the same first token |
| [`circularity`](detectors/circularity.py) | is your predictor already the answer? | a prospective law validated out-of-sample to 0.02, retracted 15 minutes later as a copy-head tautology |
| [`control_fitness`](detectors/control_fitness.py) | can your control fail, and is your positive control the right sign? | a control whose two hypotheses both predicted the same reading, and a positive control that fired inverted |
| [`prose_numbers`](detectors/prose_numbers.py) | does any code in this repository actually emit the number you wrote? | R4's fold errors and R5's whole results table, both quoted from commit messages, neither regenerable. It reports its own false-pass rate — `--power` |
| [`arm_contrast`](detectors/arm_contrast.py) | does your control arm differ from the studied arm in the property it claims to isolate, **and nothing else**? | R1's sham arm, which claims to isolate *which head* while the arms differ in *layer band* — inherited by eight rounds, found by an outside reader. Aimed at the two joints **no instrument here had ever caught** |
| [`attack_detectors`](detectors/attack_detectors.py) | do the detectors **refuse**, or do they return a clean verdict on input they cannot read? | this page claimed they refuse. Attacked with six inputs derived from their own assumptions, **three of five returned a clean verdict on garbage** — including `scale=0`, which reopened the exact hole the `scale` argument had been made required to close |
| [`hook_identity`](detectors/hook_identity.py) | does the ablation hook remove the head it *says* it removes? | ten rounds assumed that zeroing `x[h·HD:(h+1)·HD]` removes head *h* — an architecture fact across three module names, never checked. Verified exactly on **three families**: `qwen2.5-1.5b` 5.1e-07, `internlm2-1.8b` 1.1e-06, `phi-3.5-mini` 3.9e-06, every head of the layer |

```bash
python3 detectors/readout_tokens.py --selftest
python3 detectors/circularity.py    --selftest
python3 detectors/control_fitness.py --selftest
python3 detectors/prose_numbers.py   --selftest
python3 detectors/prose_numbers.py   --power      # what fraction of RANDOM numbers it clears
python3 detectors/arm_contrast.py    --selftest
```

## Running a round

```bash
pip install torch transformers numpy
python3 R1_noise_floor/run.py --model <hf-model-path> --tag mymodel \
        --rooms stone iron glass water --out results/atlas
```

Every runner gates on the readout detector before measuring, refuses if the metric is not measurable
on that model, and records any scope reduction in its own output rather than in someone's memory.

## What this does not claim

* Four models, three families, one synthetic task, attention-head ablation at one or all positions.
  Nothing here is established for MLP neurons, for SAE features, for natural text, or for methods
  other than zeroing a component's output.
* The floor **values** do not transfer. The *procedure* does.
* R5's readout axis is withdrawn: each model cleared on a different column, and the mechanism
  strengths were not matched across models, so that axis is confounded rather than null.

## Two rounds returned `NOT MET`. A separator run on the existing files says the gate was wrong, not the instrument.

R6 and R7 both stopped short of their gates. **The two rounds lost cells for two different
reasons**, and an earlier draft of this section collapsed them into one — corrected here:

| cell | why it was dropped |
|---|---|
| `phi-3.5-mini` (R6, R7) | its `mean` arm's positive control did not clear its own floor → cell declared invalid |
| `internlm2-1.8b` (R7) | its **zero** arm's `ratio_k1` is 0.98 → R1's live-sham exclusion. **Nothing to do with any positive control** |

The separator below addresses only the **first** reason. It cost zero compute — every number was
already in the checked-in results:

```
by displacement ratio   qwen2.5-1.5b 0.141 < qwen2.5-3b 0.148 < phi 0.232 < internlm2 0.272
by mean-arm readability phi 0.64 < qwen2.5-1.5b 1.03 < internlm2 2.06 < qwen2.5-3b 2.38
                                                              -> different orders
```

**The `mean` arm's failure does not track how small its perturbation is.** It tracks how readable
that *model* is at all: the mean arm sits at a stable **0.23–0.44** of the same model's zero arm on
every one of the four, and it crosses the `|PC| > 1 band sd` line only where the model's zero arm is
itself low. That is a threshold crossing a smooth quantity — not an instrument failing.

So the honest restatement, **scoped to the cells it covers**: the cells dropped for a *dead `mean`
arm* were dropped by a threshold crossing a smooth quantity, not by a broken measurement. That is
one of the two reasons. The other — `internlm2`'s band ≈ sham — is untouched by this argument and
remains a real exclusion. R8 already stopped using `mean` as a denominator and moved to a
within-cell ordering; this is evidence that the change was necessary rather than convenient, and it
is **not** evidence that every `NOT MET` was an artifact.

> **What would break this argument, stated because it is missing otherwise.** If a positive control
> can be re-admitted whenever its magnitude is "smoothly continuous" with other models', then no
> positive-control check can ever exclude anything — any failure is re-describable after the fact.
> The criterion that separates the two cases is *whether the failing arm's deficit tracks the
> intervention or the model*, and it is only checkable because four models exist. On three it would
> not have been.

*(The 0.23–0.44 fraction is **not** a matched comparison — `zero` displaces by ‖x‖ and `mean` by
`d`, which R6 measured at 14–27% of it. It says nothing about direction. What it says is that the
fraction is stable, which is the whole point.)*

## The defect ledger — the repository's own error record, exhibited rather than asserted

Every defect this project found in itself, each resolved to a commit that `make verify` re-checks
is an ancestor of `HEAD`. Not a table in a README: a hand-written ledger is a self-report.

```bash
python3 validate_defects.py
```

Every runner stamps `sha256` of its own source into the result file it writes, so *"which code
produced this number"* is a query rather than a memory —
[`validate_provenance.py`](validate_provenance.py), also in `make verify`. It is three-valued: a
matching stamp is `CONFIRMED`, a differing one is `STALE`, **no stamp at all is `UNVERIFIED`** and
falls back to git timestamps, which are weaker evidence and are reported as such. The 40 results
that predate the stamp are all `UNVERIFIED`, and git shows **12 of them were produced by code that
has since been edited**.

Downloaded the ZIP rather than cloning? The ancestry check reports **UNVERIFIED** and says so —
it does not fail, and it does not claim the rows are wrong. There is no repository to check
against, which is a fact about your directory and not about the ledger.

```
    PROVENANCE     17      whether the number has a generator at all
    SCOPE           8      which population the claim covers
    CONTROL         9      what the control arm actually holds fixed
    STATISTIC      10      what quantity the number is
    UNCLASSIFIED    4
    INTERVENTION    2      what the operation physically writes / where / when

    found by:  author reading the object 26 · instrument 12 · outside reader 7
               author attacking own detector 6 · author writing the adversary predictions 2
               author writing it up 1 · detector 6 1
```

**Not one of the 54 is a statistics error.** Every one is the same shape: a *label* carried where a
*derivation* was needed — an intervention called gentle that was smaller, a control said to hold one
thing fixed that held two, a ratio of standard deviations called a variance, a number quoted from a
commit message that no code emits.

**7 of 54 were findable only by an outside reader** — `13.0%`. That fraction was 27% at n=22 and
falls as the author keeps finding more, which is the right direction and also a reminder that a
ceiling estimated from a small sample moves. **Every count in this section is now generated from
[`defects.json`](defects.json) by `make headline`** — they were maintained by hand, and a hand-kept
tally on a ledger that grows every session is wrong one commit after it is written.

And the split is not uniform. Cross-tabulating the joint against who found it:

```
joint            by the author   by an instrument   by an outside reader
PROVENANCE            10                7                    0
SCOPE                  8                0                    2
STATISTIC              6                4                    1
CONTROL                5                1                    4
UNCLASSIFIED           4                0                    0
INTERVENTION           1                1                    0
```

**An instrument has finally caught a `CONTROL` defect — the first, at n=`54`.** It was the
provenance validator, firing on its own during a routine gate run, and what it revealed was a
false-conviction rule **inside itself**. The `--check` line asserting `0` had been written at n=`37`
precisely so the build would fail the day this happened; it failed, and the expected count was
updated rather than the check. **`SCOPE` remains `0` from instruments against `2` from an outside
reader**, and `SCOPE` is now the second-largest bin at `8`, grown almost entirely from the author
attacking his own framing. Nine detectors now exist and **not one has
ever caught a `CONTROL` or `SCOPE` defect** — those two joints were found only by another mind. That measurement is what
[`arm_contrast`](detectors/arm_contrast.py) was built from: it is aimed at the joint the instruments
had never reached, and its first selftest case is the real defect that eight rounds inherited.

### The taxonomy test now returns `ONE-JOINT-DOMINATES` — **and the threshold that produced it is a defect**

[Pre-registered](DEFECT_TAXONOMY_PREREGISTRATION.md) before any row was written, because the author
classifying his own defects will group them until a taxonomy appears. At n=22 the verdict was
`AMBIGUOUS` by one instance. At n=`54` it is **`ONE-JOINT-DOMINATES`**, because `PROVENANCE` reached
the pre-registered threshold of ≥8 and now stands at `17`.

> **That threshold is an absolute count, not a proportion, and that is a defect in the
> pre-registration itself — discovered by the gate firing.** At n=22 a bin of 8 was 36% of the
> ledger; at n=`54` a bin of `17` is `31.5%`, which is not domination
> by any reasonable reading, and the same threshold fires. **An absolute threshold on a growing
> ledger makes this verdict inevitable.** It is *not* changed here: choosing a threshold after
> seeing which verdict it produces is the single move the pre-registration exists to refuse. The
> verdict is reported as pre-registered, with its defect stated beside it.

And the three do not split evenly: **two of them are the same unnamed type** — a prediction row
derived from a *world's name* instead of from what the arms physically do, which happened in R7 and
again in R8, in the round written to fix R7. The bin set was missing a sixth joint.

> **The bins were themselves a label-carried-instead-of-derived defect.** They were taken from the
> author's own one-sentence statement of the programme — *intervention, control, statistic, scope* —
> rather than derived from the defects. The taxonomy test caught its own designer, in the design of
> the test. The two rows stay `UNCLASSIFIED`: moving them into a new bin after seeing them is how
> `AMBIGUOUS` becomes `TAXONOMY-EXISTS` without any evidence changing.

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
