# AblationNoise

**Interpretability work reports the effect of ablating a component and reads its size as evidence of
localisation. Almost none report what a *random* component of the same size does. This repository
measures that.**

Then it points the measurement at its own author's prior results, and **seven of eight published
single-head effects turn out to sit inside the noise floor** — including a head that had been
independently established as the copy head for that task. Its apparent "redundancy" was a resolution
limit, and the limit is now a number.

Everything here runs on one consumer GPU. Every round is pre-registered with a kill condition
committed **before** the run. **Six of the seven completed rounds killed, withdrew or failed to
reach the hypothesis their author preferred** — one had its verdict withdrawn by the round after it,
one was defeated by a diagnostic its author wrote to attack it, and one found two of its own
pre-registered worlds had identical predictions.

```bash
make verify     # the whole gate: 4 detector selftests, 11 recomputed numbers, 6 READMEs checked
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
| **[R1](R1_noise_floor/)** | how large is the ablation noise floor? | at k=1, *which* component you ablate explains **2.7–12.3×** more variance than *that* you ablated one — 4 models, 3 families |
| **[R2](R2_inversion/)** | how often does ablating a *known* mechanism go the wrong way? | **rare** — 0 of 4. The attractive hypothesis died |
| **[R3](R3_withdrawn/)** | is a sibling project's specificity control a single draw? | **withdrawn before spending compute** — its own records refuted the premise |
| **[R4](R4_predictability/)** | can readability be predicted from cheap observables? | across models **UNVERIFIED** — the pre-registered gate is met by 60 of 324 admissible estimators, so its own first verdict was withdrawn. Within a model the floor is a power law and **two measured points fix the curve** (12/12 held-out within 2×) |
| **[R5](R5_factorial/)** | which factor decides readability: site, readout, or mechanism size? | ablating at **every** position instead of one made the effect-to-floor ratio **worse in 6 of 6** model × readout cells |
| **[R6](R6_intervention/)** | is the floor a property of ablation, or of *zeroing*? | **NOT MET** — its own control arm reproduced R1 to **0.0% on 4 of 4 models**, then a pre-registered diagnostic showed the comparison arms move the residual stream 4–7× less, so the design cannot decide. The question stays open |
| **[R7](R7_norm_matched/)** | at a **fixed** perturbation size, does the *direction* change readability? | **NOT MET** on the gate (2 of the 4 cells were droppable). But with displacement matched to **0.00%**, a known effect is **least** readable in the on-distribution direction and **most** readable in the zeroing direction, in **4 of 4** cells — the opposite of what the off-manifold objection predicts |

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
two of four cells were droppable, one for a dead arm and one by R1's own live-sham exclusion. But
the part that needs no gate is unambiguous — **in 4 of 4 cells a known effect is *least* readable in
the on-distribution direction and *most* readable in the zeroing direction.** The off-manifold
objection predicts the reverse. It is one family short of the pre-registered bar, so it is reported
as an ordering across 4 models and 3 families, not as a verdict.

What both rounds established on the way: the zero arm reproduced R1's `ratio_k1` to **0.0% on four
models out of four, twice**, through two independently rewritten measurement paths. R1's number is
not an artifact of R1's own code.

## The result that is most useful to someone else

**A floor cannot be looked up.** Changing four English nouns in the answer vocabulary moved it 1.7×
on a fixed model; across models the exponent spans 0.3–0.8 and the scale spans 8.8× on an identical
task. But within a model it is a clean power law in set size (R² 0.935–0.985), so **measuring two set
sizes fixes the whole curve** — two conditions instead of a sweep.

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

```bash
python3 detectors/readout_tokens.py --selftest
python3 detectors/circularity.py    --selftest
python3 detectors/control_fitness.py --selftest
python3 detectors/prose_numbers.py   --selftest
python3 detectors/prose_numbers.py   --power      # what fraction of RANDOM numbers it clears
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
| **Does it hold off a synthetic task?** | scope of every round | a natural-text task with a known mechanism. The synthetic binding task was chosen so the answer key is not arguable, which is also why it is not a claim about language modelling |

One item that is **not** open: whether R1's number is an artifact of R1's own code. R6's zero arm
reproduced it to **0.0%** on **four models out of four**, through a completely rewritten measurement
path.

## Licence

MIT.
