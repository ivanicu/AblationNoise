<!-- unbacked-ok: 2.62 24 27.58 17.2 35 -- the fresh-clone verification's wall time, peak memory and
 false-pass rate, plus the earlier rate and the ceiling. Measured once on 2026-07-28 against a clone of the published remote; they
 describe that run and cannot be regenerated from checked-in data.
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
network, no dependencies, `2.6 s` on a stock `python3` with `numpy` confirmed absent. It was run
from a fresh clone of this remote on 2026-07-28, not asserted.

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
I_all        0.3196            0.4004            0.6782         6.67
```

**Not enriched under either intervention — and `T_pub` is *below* the null median in both.** The
eight published heads are, on average, **less** extreme than random heads from the same layers.

> **The instrument was checked before the null was believed.** Positive control: the actual top-`8`
> by `|centred|` is reached by only `1` of `50000` matched sets, so the test can separate. Null calibration: `200`
> random matched sets fall under `0.05` at a rate of `0.035` against a nominal `0.05`.
>
> **Layer matching is not decoration.** The eight sit in `L16`–`L22`, magnitude varies strongly with
> depth, and an unmatched null would manufacture enrichment out of nothing but where the heads live.

**Both distributions are heavy-tailed** — excess kurtosis `7.31` and `6.67` — which is why the `2σ`
floor is not a test in either arm and the percentile replaces it.

### And the descriptive picture the scalar floor gave

`L22H7` was independently established, by a prior experiment, as the copy head for this task.
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
> independently established role. **One point is an anecdote.**
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
