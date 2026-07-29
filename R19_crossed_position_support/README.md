<!-- unbacked-ok: 0.4906 0.5871 -- the WRONG-SCOPE values, quoted verbatim inside their own correction so the error can be read against the right ones; no generator emits them, which is the point. 0.5616 -- the reviewer's independently computed ICC(3,1), their number not mine, same class as the other reviewer-computed figures exempted here. 0.669 0.094 0.62 5.35 -- an independent reviewer's own measurements of the design effect, computed during its audit from the raw result file. No generator here emits them because this repository did not compute them; what it DID compute is the group-clustered interval beside them, which is emitted by tools/clustered_ci.py. 0.0066 -- the WRONG hand-subtracted value, quoted verbatim inside its own correction so the error can be read against the emitted 0.0065. No generator emits it, which is the point. 23.6 -- the result file's size in megabytes, a measurement of a file rather
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

**`H-support` fails on all three metrics.** *"A head"* and *"a head's write at the final query
position"* are different objects — and that is now a confirmatory result, not an exploratory one.

> **⚠ `D134` — this sentence said "fails all four components" and that is FALSE**, contradicted by
> the table six lines above it. `published_agree` requires `8/8` and observes `7/8`, **`8/8`**,
> **`8/8`** — it **passes** on `room_set_kl` and `behavioural_flip`. Ten of twelve components fail,
> not twelve. An independent reviewer found it; no instrument here can, because the claim is a count
> in prose over a table the emitter never sums.
>
> **And the component that passes, passes for a bad reason.** `agree` counts heads where
> `(|centred| > floor)` matches across scopes, and **none of the eight clears either floor on those
> two metrics** — every agreement scored is `False == False`. The check cannot distinguish *"the two
> supports agree"* from *"neither support detects anything"*. Filed as `D135`.

### The last escape hatch, closed with numbers from this same run

`H-support` fails because `Spearman(final, all)` is `0.6778` against a registered `0.9`. The only
remaining deflation is that `0.6778` is depressed by **measurement error** rather than by the two
supports being different objects. Both reliabilities are split-half over R19's own `64` bases — same
task, same items, same model, same run — so the ceiling is measured here rather than borrowed.

```
metric                  raw     ceiling    disattenuated   still below 0.9
signed_margin_drop     0.6778        0.9434        0.7185          yes
room_set_kl            0.5314        0.9863        0.5388          yes
behavioural_flip       0.4991        0.9056        0.5512          yes
```

**`H-support` survives correction on all three metrics.**

> **WARNING `D138` — the CIs in the table above resample `64` bases as if independent, and the
> design has `8`.** `query = elig[b % 8]` and `want = rooms[b % 4]`, and `4` divides `8`, so the
> query name **perfectly determines the answer room**: `8` distinct cells replicated `8` times.
> An independent reviewer measured the between-group share of base-level variance at a median of
> `0.669` against a random-grouping null of `0.094` — `ICC` about `0.62`, design effect about
> `5.35`, **effective `n` about `12`, not `64`**. Resampling the `8` groups instead:
>
> ```
> metric                  point   base-resample CI       group-clustered CI    width
> signed_margin_drop     0.6778   [+0.6117, +0.7014]   [+0.5642, +0.7518]   2.03x
> room_set_kl            0.5314   [+0.5016, +0.5745]   [+0.4975, +0.5764]   1.09x
> behavioural_flip       0.4991   [+0.4140, +0.5421]   [+0.3936, +0.5482]   1.20x
> ```
>
> **The reviewer estimated about `2.3` times wider from a different computation; this gives
> `2.03` times and `[+0.5642, +0.7518]`** — an independent reproduction of an adversarial finding by a
> second method. Both intervals are emitted; hiding the narrow one would hide the size of the
> error.
>
> **The kill branch did not fire.** Even the honest upper bound is `0.7518`, nowhere near the
> registered `0.9`, on any metric. **`H-support` survives the correction it needed.** And the
> clustering penalty is `2.03` times on the primary metric against `1.09` and `1.20` on the
> others — the aliasing bites hardest exactly where the headline is.

> **⚠ `D133` — the first version of this table used the WRONG CEILING, in the direction that
> flattered the conclusion, and it was wrong twice over.**
>
> `analyze.py:187` correlates `|tau − mu|` — a **centred magnitude** — using **Spearman**. The
> ceiling first used here was the **Pearson** reliability of the **signed** `tau`. Two mismatches at
> once: wrong coefficient family, and wrong quantity. Taking `|centred|` destroys information, so
> the signed reliability is **higher** than the right one and every disattenuated value came out
> **lower**, making the gap to `0.9` look safer than it is.
>
> ```
> superseded, do not quote:
> signed_margin_drop   ceiling   0.9904  ->  disattenuated   0.6844
room_set_kl          ceiling   0.9990  ->  disattenuated   0.5320
behavioural_flip     ceiling   0.9849  ->  disattenuated   0.5068
> ```
>
> **The conclusion does not move — all three are still below `0.9`** — but the primary metric's
> correction was understated by `0.0341`. Found by writing `ADVERSARY.md`'s `A19`, which predicted
> the Spearman/Pearson half; **the wrong-quantity half was not predicted and surfaced only while
> chasing it.** The correct reliabilities are frozen in
> `results/r19_reliability_of_magnitude.json` and `r19()` reads them.

> **⚠ `D140` — the registered ICC is the WRONG MODEL for this design, and the right
> one crosses the threshold.** `icc1()` is `ICC(1,1)`, the one-way model, valid when each
> subject is rated by a *different* randomly drawn set of raters. Every base here is measured
> at the **same** `8` positions — fully crossed, where `ICC(3,1)` is appropriate.
> `ICC(1,1)` charges the position **main effect** to error, and `baseline_margin_by_pos`
> spans `4.02` to `0.51`.
>
> ```
> metric                ICC(1,1)   ICC(3,1)     delta   crosses 0.50 under 3,1
> signed_margin_drop     0.4734     0.5599   +0.0866   True
> room_set_kl            0.2907     0.3656   +0.0748   False
> behavioural_flip       0.0282     0.0335   +0.0054   False
> ```
>
> **The pre-registration named `ICC(1,1)` explicitly, so the registered verdict STANDS and
> is not switched here.** This is different from a wrong number: **the pre-registration
> registered the wrong MODEL for its own design**, and a threshold cannot protect against
> that. `H-position` stays `FALSE` regardless — it fails decisively on the third
> component below.
>
> **`D142` — three computations now agree, and the first version of my tool did not.**
> It read the `.final` scope while `analyze.py:215` uses `.all`, returning `0.4906`/`0.5871`
> against the analysis's `0.4737`. That looked like implementations disagreeing and was
> **me comparing unlike with unlike** — the same defect a reviewer had caught in
> `margin_normalisation()` an hour earlier. Corrected: `ICC(1,1)` `0.4734` against the
> analysis's `0.4737`, `ICC(3,1)` `0.5599` against the reviewer's independent `0.5616`.
>
> **⚠ `D136` — the component that actually decides `H-position` was never on this page, and the box
> explaining `H-position` was deleted by one of my own slice edits without my noticing.**
> `H-position` has three registered components. The third —
> `Spearman(line-0 rank, position-averaged rank) >= 0.8` — reads **`0.3494`**, missing by **`0.4506`**,
> which is **seventeen times** the ICC margin. On the other two metrics it is `-0.2541` and `-0.1903`. It
> sits in the analysis JSON as `spearman_line0_vs_posavg` and `r19()` emitted a bespoke
> `icc_margin_below_threshold` for the near-miss while dropping the decisive one.
>
> **The direction is against my own framing** — it makes a decisive `FALSE` read as a
> resolution-limited near-miss — but a stated framing the code contradicts is a defect whichever way
> it points.
>
> **Restored, because the ICC margin is still worth reading:** the primary metric's ICC misses the
> registered `0.50` by `0.0263`, and [`ADVERSARY.md`](../ADVERSARY.md)'s `A16`, written before the
> data, predicted the ICC would land in `[0.2, 0.8]` where `64` bases cannot separate the hypotheses.
> **The rule says `FALSE` and the rule is honoured.** Changing a threshold because the result landed
> near it is what pre-registration exists to prevent — and on the third component it is not near at
> all.

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

Seven seconds, standard library only.

> **⚠ `D137` — this line said the result file "is checked in" and `git ls-files` did not list it.**
> An independent reviewer ran the command; no instrument here did. The `23` MB file is tracked now.
> **Two further files `headline.py` consumes — `r19_split_half_reliability.json` and
> `r19_reliability_of_magnitude.json`, the two numbers that close this round's headline escape
> hatch — were produced by a scratchpad script and generated by NOTHING IN THE REPOSITORY.** Their
> emitters are checked in under `tools/`. *"A claim whose generator does not exist is
> indistinguishable from a claim that was never true"* is `headline.py`'s opening paragraph; it was
> true of its own two most load-bearing files.
