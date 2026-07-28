# Methods — the rounds, the instrument, and how to run one

> Split out of `README.md` on 2026-07-28 without rewriting.

> **Not every `R<n>` directory is an experiment.** `R16` (how the audited set was chosen),
> `R17` (an attack on the headline that moved nothing) and the depth-bias section of `R12` are
> **data audits and estimand corrections**. They are kept at their numbers because the commit
> history refers to them, and they are marked here so the count of "rounds" is not read as a
> count of experiments. The experiments are `R1`, `R2`, `R4`–`R15`, `R18` and — **not yet
> run** — `R19`.

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

