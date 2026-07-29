<!-- unbacked-ok: 23.6 -- the result file's size in megabytes, a measurement of a file rather
 than a generated value; same class as the runtime figures exempted at the top of README.md. -->
# R19 — the crossed *position × intervention-support* scan

**This repository's only confirmatory experiment.** Pre-registered in
[`PREREGISTRATION.md`](PREREGISTRATION.md) with six amendments, all committed before the data
existed. It landed on 2026-07-28 **at the eleventh attempt** — ten preemptions, survived by a
per-layer checkpoint.

```
64 base instances × 8 query positions × 2 nuisance permutations = 1024 prompts
28 layers × 12 heads × 2 intervention supports = 672 cells
statistical unit: the BASE INSTANCE, n = 64 — never the prompt
baseline accuracy 0.7412    mean margin +1.6357
```

## The four hypotheses, separate verdicts, three metrics reported separately

```
                       signed_margin_drop      room_set_kl       behavioural_flip
Spearman final×all          0.6778               0.5314              0.4991
  cluster-bootstrap CI  [0.6117, 0.7014]   [0.5016, 0.5745]   [0.4140, 0.5421]
published_agree              7/8                  8/8                 8/8
centroid shift             0.0854               0.0988              0.1704
top-10 overlap              4/10                 5/10                6/10
H-support                   FALSE                FALSE               FALSE
```

**`H-support` fails all four components on all three metrics.** *"A head"* and *"a head's write at
the final query position"* are different objects — and that is now a confirmatory result, not an
exploratory one.

```
ICC median                 0.4737               0.2921              0.0289     (threshold 0.50)
p_position                 0.8755               0.6930              0.7653
H-position                  FALSE                FALSE               FALSE
```

> **⚠ Read `H-position` with its margin.** The primary metric's ICC misses the registered `0.50` by
> **`0.0263`**. [`ADVERSARY.md`](../ADVERSARY.md)'s `A16`, written before the data, predicted the ICC
> would land in `[0.2, 0.8]` — the band where `64` bases cannot separate the hypotheses — and that
> *"the honest verdict is therefore UNRESOLVED."* **The rule says `FALSE` and the rule is honoured;
> the prediction that the rule would not resolve it was correct.** Both are reported. Changing the
> threshold now because the result landed near it is the thing pre-registration exists to prevent.

```
H-published   final p     0.7914               0.3613              0.0704
              all   p     0.9337               0.4623              0.4245
                    NOT enriched — both scopes, all three metrics
H-depth       UNTESTED by pre-registration: two models is n = 2
```

## Two registered bets, one lost

**`L17H0` — LOST.** The pre-registration staked it on the top `10` of `168` by
`|centred tau^all|`, and said in its own words: *"if it fails, the three-instrument convergence was a
coincidence over `168` heads and this line is the record that I bet on it."*

```
all     rank  37 of 168    centred tau +0.2713    WRONG
final   rank  45 of 168    centred tau -0.0958    WRONG
top10 (all): L18H0 L19H6 L16H4 L18H5 L16H2 L17H2 L26H7 L17H3 L19H9 L16H5
```

Attention selected it into the published eight, `R18`'s `I_all` ranked it `4th`, the OV circuit
ranked it `3rd`. **On an independently constructed task it is `37th`.**

**The OV-copier prediction — `NOT CONFIRMED`.** Both halves were required:

```
room_set_kl          T 0.0231   matched-layer null median 0.0310   one-sided p 0.9603   FAIL
signed_margin_drop   T 0.1561   null median 0.1964                 one-sided p 0.8817   PASS
```

The `25` frozen OV-perfect room copiers do not carry *more* room-set KL under `I_all` — they carry
**less**.

## What R19 established, and what it did not

**Established.** `H-support` is false, confirmatorily, on a task built independently of the eight.
The split-half reliability of both scopes is high — `0.9918` final, `0.9891` all — which **killed the
`scalar-up-to-scale` rival** ([`SHAPE_RANK_PREREGISTRATION.md`](../R11_instrument_noise/SHAPE_RANK_PREREGISTRATION.md),
Amendment 2).

**Not established.** `H-depth`, by design. `H-position`, by resolution. And **no mechanism** — R19
measures what the intervention does, not why.

## Known defects in this round, filed before the analysis was read

| | |
|---|---|
| [`D131`](../DEFECT_LEDGER.md) | the **saturation gate** counts cells where the correct room is not the argmax, which is already true for every baseline-incorrect item. Its floor is the baseline error rate `0.2588`, and the observed all-scope rate is `0.2618` — `0.0030` above a floor set by the task's difficulty rather than by the intervention. (The final-scope rate sits *below* the floor; that figure comes from the live checkpoint and is recorded, with its exemption and its reason, in [`PREREGISTRATION.md`](PREREGISTRATION.md) Amendment 6 rather than repeated here unbacked.) Metric `2` is correctly baseline-referenced and unaffected |
| [`D126`](../DEFECT_LEDGER.md) | the checkpoint has **no concurrency lock**; a second runner would silently interleave |
| [`D129`](../DEFECT_LEDGER.md) | `_CODE_VERSION = sha256(run.py)`, so the runner could not be improved while the job was partially done |
| `D132` | the `L17H0` bet was **registered in prose with no scorer** — `analyze.py`, written before the data, never computed it. Added now |

## Reproduce

```bash
python3 R19_crossed_position_support/analyze.py \
        R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json
```

Seven seconds, standard library only. The `23.6 MB` result file is checked in.
