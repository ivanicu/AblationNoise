# R1 — the ablation noise floor

**Question.** Ablation effects are read as evidence of localisation. What does a *random* component
set of the same size do?

**Verdict.** `K1-COMPONENT-CHOICE` — at k=1, *which* head you ablate accounts for **2.7×–12.3×** more
variance than *that* you ablated one, on four models across three families.

| model | family | margin | sd(k=1) | floor | sham | ratio_k1 | |
|---|---|---|---|---|---|---|---|
| qwen2.5-1.5b | Qwen | 3.287 | 0.275 | 0.084 | 0.019 | **4.3×** | pass |
| qwen2.5-3b | Qwen | 6.120 | 0.159 | 0.026 | 0.004 | **6.7×** | pass |
| phi-3.5-mini | Microsoft | 13.046 | 0.207 | 0.016 | 0.001 | **12.3×** | pass |
| llama-3.1-8b | Meta | 5.061 | 0.051 | 0.010 | 0.004 | 2.7× | fail |
| internlm2-1.8b | InternLM | 0.561 | 0.031 | 0.056 | 0.057 | 1.0× | **flagged** |

internlm2 is excluded by a rule written into Amendment 1 **before** it ran: a model whose sham arm is
not inert cannot have its ratio read, because the sham was drawn from a live region. Its 1.0× is not
evidence in either direction.

**The threshold is not doing the work.** Sorted informative ratios are 2.7 / 4.3 / 6.7 / 12.3, so the
verdict holds for any threshold up to 4.3× — the chosen 3.0 sits inside that band, not at its edge.

## Applied to the author's own prior results

2 sd of a random single head in the studied band is **0.442 margin units**. Against that, of eight
previously measured single-head effects, **seven are inside the floor** — including the head an
earlier experiment had independently proved was the copy head (−0.132, a third of the floor). The
largest effect in the set clears by 6%.

## Two amendments, both committed before the runs they govern

* [AMENDMENT 1](AMENDMENT_1_statistic.md) — the original gate took a median over set sizes, and the
  per-size rows revealed that the median pooled two regimes whose trend **reverses between models**.
  Statistic changed on the record; the two verdicts already taken may not be cited as evidence for
  the amended gate.
* [AMENDMENT 2](AMENDMENT_2_report_both.md) — the dimensionless floor moves for two reasons and one
  of them is the denominator. At k=5, changing only the answer vocabulary made the raw noise **fall**
  18% while the floor **rose** 11%. Raw sd must be reported beside every floor.
