# R14 — does the model bind the name, or copy line 0?

Written and committed **before the probe runs**. 2026-07-28.

[R13](../R13_task_audit/) established that this repository's task is **fixed-position retrieval**:
the query is always `Alice`, her fact is always **line 0**, and `copy the room from line 0` scores
`100%` without matching a name. **The task cannot distinguish position-copying from name-binding,
because the two strategies agree on every item it contains.**

R14 makes them disagree.

## The intervention — one line of the prompt builder

Shuffle the order in which the eight fact lines are emitted, per item. Nothing else changes: the
same bindings, the same question, the same readout, the same seeds. **The queried person's fact now
lands at a uniformly random line index instead of always at `0`.**

```
ORIGINAL   line 0 is always the answer's fact
SHUFFLED   the answer's fact is at a uniformly random line 0–7
```

A model that binds the name is unaffected. A model that copies line `0` drops to chance, because
line `0` is now some other person's fact — and each room appears exactly twice among eight persons,
so chance is `25%`.

## The cheapest decisive thing first

**Baseline accuracy only — no ablation.** `120` forward passes. If the model cannot do the shuffled
task at all, an exhaustive ablation scan over it measures nothing and must not be run.

## What each outcome means — fixed now

Let `A_orig` and `A_shuf` be top-1 accuracy over the **same** seed window, `3000–3400`.

| outcome | reading |
|---|---|
| `A_shuf ≥ 0.9 × A_orig` | **`BINDING`** — position was not what the model used. The twelve rounds' measurements describe a task the model solves by binding, and the R13 rescoping is a statement about what the task *could* have permitted, not about what happened. |
| `A_shuf ≤ 0.35` | **`POSITION`** — the model was reading line `0`. Every "copy head" claim in this repository is a claim about **position**, and `L22H7` is a position head. |
| in between | **`MIXED`** — report the number, claim neither. |

`0.35` is `25%` chance plus a `10`-point margin, chosen before the run and not tuned to a result.

> **KILL, and it points at my own last two steps:** if `A_shuf ≥ 0.9 × A_orig`, then R13's finding
> is real about the task and **wrong as an insinuation about the model** — I will have spent two
> steps implying the model exploits a degeneracy it does not exploit. That outcome must be reported
> as loudly as the other one.

## Strongest confound, written before the run

**Shuffling changes more than position.** It also changes which facts are adjacent, and it moves the
answer's fact *away from* the start of the context — a region models attend to differently for
reasons unrelated to this task. A drop in `A_shuf` is therefore consistent with *position-copying*
**and** with *a general recency/primacy effect on retrieval difficulty*.

**Control in the same run:** report accuracy **as a function of the answer's line index**. Under
position-copying, accuracy should be near `100%` when the answer happens to land at line `0` and
near chance elsewhere — a step. Under a primacy effect it should decay smoothly with distance. The
two shapes are different and the same `120` items measure both.

## What R14 cannot do

* **It does not identify a mechanism.** It separates two task-level strategies, not two circuits.
* **One model to start** (`qwen2.5-1.5b`), one task, one vocabulary.
* **A `BINDING` verdict does not restore the word "binding" to the other twelve rounds.** They were
  measured on the *unshuffled* task; what the model does there is what this probe reports, and any
  head-level claim would still need the exhaustive scan re-run on the shuffled task.
