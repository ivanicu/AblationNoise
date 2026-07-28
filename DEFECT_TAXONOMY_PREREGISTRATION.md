# PRE-REGISTRATION — does this project's own defect record have a TAXONOMY, or is it 13 one-offs?

Written 2026-07-28, **before any defect is classified**, and before the classifier exists.

---

## Why this is a frontier action and not bookkeeping

The stated north star for this line is: *make the physical content of an interpretability claim
checkable, and measure how often the label and the operation disagree in published work.* That whole
programme rests on a premise nobody has tested:

> **the defects found here fall into a small number of RECURRING joint types.**

If they do, the joints can be extracted from a paper and a rate can be measured. If they are
thirteen unrelated one-offs, there is nothing to extract, the "rate" is a rate of nothing, and the
north star as stated is **wrong** — the deliverable would be the instrument, not a measurement.

## The confound, written before the classification

**I am classifying my own defects, and I will unconsciously group them until a taxonomy appears.**
So the bins are **fixed here, in advance**, and they are not derived from the defects. They are the
four joints of the claim chain named in the north star, plus one for provenance:

| bin | the label attaches to | example shape |
|---|---|---|
| `INTERVENTION` | what the operation physically writes / where / when | "mean-ablation is gentler" when it is 4–7× smaller |
| `CONTROL` | what the control arm actually holds fixed | "the sham controls for *that* you ablated" when it also controls for *where* |
| `STATISTIC` | what quantity the number is | "variance" for a ratio of standard deviations |
| `SCOPE` | which population / cells / regime the claim covers | one label over two different inclusion properties |
| `PROVENANCE` | whether the number has a generator at all | a figure quoted from a commit message, unregenerable |
| `UNCLASSIFIED` | **fits none of the above** | — |

**`UNCLASSIFIED` is the test.** A taxonomy that needs a large "other" bin is not a taxonomy.

## Prediction matrix

| world | signature |
|---|---|
| **W_A — TAXONOMY EXISTS** | ≥3 bins hold ≥2 instances each **AND** `UNCLASSIFIED` ≤ 2 |
| **W_B — THIRTEEN ONE-OFFS** | `UNCLASSIFIED` ≥ 5 **OR** no bin holds ≥2 |
| **W_C — ONE JOINT DOMINATES** | a single bin holds ≥ 8 |
| **AMBIGUOUS** | anything else — report the counts, claim neither |

These rows differ, and they were compared as tuples before being written down — the check R8's
matrix failed.

## Retraction commitment

**If `W_B` fires, the north star stated to Ivan on 2026-07-28 is wrong and is withdrawn in the same
commit as this result.** Not softened, not deferred. The fallback position — that the deliverable is
the instrument and its self-calibration, with no rate — is a smaller claim and would be stated as
such.

**If `W_C` fires**, the north star survives but narrows: the programme is about one joint, not four,
and the extractor becomes far cheaper and far less interesting.

## Admission rule for a defect — pointer or it does not enter

Every row must carry a **commit SHA in this repository** that is an ancestor of `HEAD` and whose
message records the defect. A defect I remember but cannot resolve to a commit does not enter the
ledger, however sure I am of it. That rule exists because this ledger's entire value is that it is
**exhibited rather than asserted** — the exact criticism an outside reader made of the repository's
"seven of eight" claim, which is stated nowhere in the repo and shown nowhere at all.

`validate.py` re-checks every SHA against `git merge-base --is-ancestor` and fails the build on a
row that does not resolve. A hand-written ledger is a self-report; one that fails the build when it
drifts is not.

## What this cannot do

* n = the defects of **one project by one author over two days**. It bounds nothing about
  published work. It decides only whether the bins are worth building an extractor for.
* The bins were chosen by the same mind that made the defects. An outside reader may find they
  carve badly; that is the next adversarial pass, not this one.
* Finding a taxonomy here does **not** establish that published papers fail at the same joints —
  that is L5, and it needs papers.
