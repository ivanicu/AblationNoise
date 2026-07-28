# AblationNoise

**Interpretability work reports the effect of ablating a component and reads its size as evidence of
localisation. Almost none report what a *random* component of the same size does. This repository
measures that.**

Then it points the measurement at its own author's prior results, and **seven of eight published
single-head effects turn out to sit inside the noise floor** — including a head that had been
independently established as the copy head for that task. Its apparent "redundancy" was a resolution
limit, and the limit is now a number.

Everything here runs on one consumer GPU. Every round is pre-registered with a kill condition
committed **before** the run, and three of the five rounds killed the hypothesis their author
preferred.

---

## The rounds

Each round is a folder: its pre-registration, its amendments, its runner, its results.

| | question | verdict |
|---|---|---|
| **[R1](R1_noise_floor/)** | how large is the ablation noise floor? | at k=1, *which* component you ablate explains **2.7–12.3×** more variance than *that* you ablated one — 4 models, 3 families |
| **[R2](R2_inversion/)** | how often does ablating a *known* mechanism go the wrong way? | **rare** — 0 of 4. The attractive hypothesis died |
| **[R3](R3_withdrawn/)** | is a sibling project's specificity control a single draw? | **withdrawn before spending compute** — its own records refuted the premise |
| **[R4](R4_predictability/)** | can readability be predicted from cheap observables? | **no** across models (0/5 folds) — but within a model the floor is a power law, so **two measured points fix the curve** (12/12 held-out within 2×) |
| **[R5](R5_factorial/)** | which factor decides readability: site, readout, or mechanism size? | ablating at **every** position instead of one made the effect-to-floor ratio **worse in 6 of 6** model × readout cells |

## The result that is most useful to someone else

**A floor cannot be looked up.** Changing four English nouns in the answer vocabulary moved it 1.7×
on a fixed model; across models the exponent spans 0.3–0.8 and the scale spans 8.8× on an identical
task. But within a model it is a clean power law in set size (R² 0.94–0.99), so **measuring two set
sizes fixes the whole curve** — two conditions instead of a sweep.

**And ablating harder makes it worse.** When an ablation shows nothing the reflex is to cut more.
Across three models and both readouts, moving from one position to every position widened the floor
2.4–5.2× while the effect changed by 0.90–1.94×. Six of six cells got *less* readable.

## The detectors

Each was born from a specific failure in this work, carries its own positive control, and refuses
rather than degrading. A detector that has never fired is not a detector, so each one's `--selftest`
replays the real incident that produced it.

| | asks | born from |
|---|---|---|
| [`readout_tokens`](detectors/readout_tokens.py) | does your readout distinguish the answers you are scoring? | a run reported `n=0` because a SentencePiece tokenizer gave all four answers the same first token |
| [`circularity`](detectors/circularity.py) | is your predictor already the answer? | a prospective law validated out-of-sample to 0.02, retracted 15 minutes later as a copy-head tautology |
| [`control_fitness`](detectors/control_fitness.py) | can your control fail, and is your positive control the right sign? | a control whose two hypotheses both predicted the same reading, and a positive control that fired inverted |

```bash
python3 detectors/readout_tokens.py --selftest
python3 detectors/circularity.py    --selftest
python3 detectors/control_fitness.py --selftest
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

## Licence

MIT.
