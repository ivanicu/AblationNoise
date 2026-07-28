# R13 — audit the task, not the measurement

Twelve rounds, four detectors, `65` logged defects and a pre-registration apiece, all aimed at
**how things were measured**. None of them was ever pointed at **what was being measured**. R13 is
that, and it needed no model.

## What the task actually requires

Every runner chooses its query as *the first person that is a single content token under this
model's tokenizer*, and every binding assigns **all eight** persons — so the query is `single[0]`,
identical on every item. The prompt's fact lines are emitted in fixed `PERSONS` order, so that
person's fact sits at a **fixed line index**.

```
line 0: Alice owns the wand. The wand is in the rust room.     <- the answer, every item
line 1: Bob   owns the pill. The pill is in the rust room.
...    six more facts, never queried by anything
line 8: Question: Which room should Alice go to find their object?
line 9: Answer: The
```

> **The correct answer is always the room named in the first sentence.** `copy the room from line 0`
> scores `100%` without matching a name.

The **labels** are balanced — across `400` seeds the four rooms take `23.5%`–`26.2%`. It is the
**structure** that is degenerate.

## Is it uniform across models? — `probe_query_position.py`

It had to be checked, because `single[0]` depends on the **tokenizer**. A model where `Alice` is not
a single content token would be asked about someone else, at a different line, and
[R1](../R1_noise_floor/)'s cross-model ratio would be comparing two different tasks.

```bash
python3 R13_task_audit/probe_query_position.py --artifacts <dir>   # tokenizers only, no weights
```

```
single-token persons   qwen2.5-1.5b 8/8   qwen2.5-3b 8/8   phi-3.5-mini 6/8   internlm2-1.8b 4/8
distinct query LINE indices across 8 model × vocabulary cells:   [0]
```

**Uniform.** The counts differ; `Alice` is single-token under all four; every model is asked about
line `0`. Cross-model comparisons stay commensurable — **and the degeneracy is everywhere.**

> **The first version of this probe was wrong**, and the way it was caught is the point. It
> reimplemented the runner's tokenization instead of reusing it, dropped the `prefix_len`
> adjustment, and reported `0` of `8` single-token persons for `phi-3.5-mini`. The actual run had
> already printed `6` to its job log. **The disagreement with a number the object had emitted is the
> entire reason it surfaced** — the same *match rule is not the concept* defect this repository keeps
> finding elsewhere, committed while investigating that exact class.

## What this does and does not do to the other twelve rounds

| | |
|---|---|
| **unaffected** | every comparison **between** heads — the floor, the ranking, the counts, the item-noise, the null's centring. All heads face the same task, so these remain exact statements *about this task*. |
| **unaffected** | every methodological finding: exhaustive vs hypothesis-driven, the uncentred null, the detector defects, the provenance chain, the fresh-clone verification. |
| **rescoped** | the *description*. `L22H7` was called a **copy head**; on this task it may be copying from **position `0`** rather than resolving a name, and **no measurement here can tell those apart** — the two strategies agree on every item the task contains. |

## What R13 does not claim

* **It is not a kill.** Nothing measured becomes wrong; a set of sentences becomes narrower.
* **It does not show the model uses position.** It shows the task cannot distinguish. Asserting the
  positional strategy would be the same error in the opposite direction.
* **The repair is obvious and is not done here:** vary the queried person, so the answer's line index
  varies with it. That separates position-copying from name-binding for the first time, and it is
  the one experiment this repository most owes.
