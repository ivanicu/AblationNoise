# Pre-registration — what IS the indirect term? Attribute it to component classes, and refuse to name a mechanism for it

Written 2026-07-29, **before the statistic was computed**, committed alone so git ordering rather
than my word establishes that the thresholds preceded the numbers.

## The claim under attack is the one I published two hours ago

`R20` established that `I_final(L,h)` is dominated by something other than the head:

```
median |total| 0.0663   median |direct| 0.0199        ratio 3.3251x
sign(total) == sign(direct)   79 of 168               p 0.4876, a coin flip
pooled Spearman(|total|, |direct|)                    +0.0166
```

and killed both named mechanisms — self-repair (`|total| < |direct|` required, opposite holds at
`p = 2e-06`) and systematic amplification (same-sign required, `47%` observed).

**So there is a term that is `3.3x` the head's own contribution, and this repository has no account
of it at all.** The last time it had a gap this shape it named a mechanism — *"that is
compensation"* — and spent a session pointing at the wrong experiment. **This round names no
mechanism. It attributes the term to component classes, which is a measurement, and stops there.**

## The three worlds

| | |
|---|---|
| **World MLP** | the response is the MLPs at the final position recomputing on a changed input. Then the indirect term is a *feed-forward* fact and no attention-level story is needed. |
| **World ATT** | the response is later attention heads writing differently — their queries changed, so they read different positions. Then removing a head at the final position changes *what the model looks at*, and single-head attribution is entangled with routing. |
| **World NORM** | the response is mostly the final RMSNorm rescaling everything, because removing a head changes `‖res‖`. Then it is not a "response" in any interesting sense — it is a global gain change, and the entire `3.3x` is an artefact of measuring a margin after a normalisation. |

**World NORM is the deflationary one and it is live**: `R20` charged renormalisation to
`direct_renorm`, but only the part caused by removing `a_h` itself — **not** the part caused by every
downstream component then changing. Those are different terms and this repository has never
separated them.

## The decomposition, and it is an exact identity rather than an estimate

The final pre-norm residual is a sum over components — the embedding, every attention head's write
at the final position, every MLP's write, and the biases:

```
margin(res)  =  rms(res) * SUM_c  (u_cor - u_comp) . (g (*) w_c)
```

`rms(res)` is a **scalar**, so for a fixed comparator the margin is **exactly additive** over
components. Write `k = rms(res)` and `v_c = (u_cor - u_comp).(g (*) w_c)`. Ablating head `h` gives

```
margin(res') - margin(res)  =  k' * SUM_c (v'_c - v_c)   +   (k' - k) * SUM_c v_c
                               \_______ component response ______/   \___ renorm gain ___/
```

Every term is measured, and their sum **must** reproduce the measured total. Classes:

```
OWN      the ablated head's own write            -- this is R20's `direct`, recovered
ATT      every other attention head              335 members
MLP      every MLP block                          28 members
EMB      embedding + biases + anything residual
NORM     the (k' - k) global gain term
```

## Cost, stated before spending it

`168` band heads x `120` items = `20,160` forward passes, half of what `R10` already spent on this
same model and item set. Per-layer atomic checkpointing, because this box has `SIGKILL`ed long GPU
jobs `11` times in one round.

## Registered thresholds

Population: the `168` band heads `L14`–`L27` of `qwen2.5-1.5b`, R10's own `120` baseline-correct
items, `I_final` support, `signed_margin_drop`, fixed clean comparator.

Share of a class = its **signed** summed contribution divided by the summed contribution of all
non-`OWN` classes, taken in absolute value and normalised — i.e. `|share_C| / SUM_C |share_C|`,
median over the `168` heads.

| verdict | rule |
|---|---|
| **MLP-DOMINATED** | median share of `MLP` `>= 0.50` |
| **ATTENTION-DOMINATED** | median share of `ATT` `>= 0.50` |
| **RENORM-DOMINATED** | median share of `NORM` `>= 0.50` |
| **MIXED** | no class reaches `0.50` |
| **UNVERIFIED** | either identity control below fails |

## Positive controls, both exact identities

1. **The decomposition must reproduce the measured total.** `OWN + ATT + MLP + EMB + NORM` must
   equal `R10`'s frozen `total(h)` for every head, to numerical precision. Gate:
   `max |sum - total| <= 0.05 x` the band's between-head sd of `total`, the same limit `R20` used.
   **This is not a soft check — the decomposition is an identity, so any real discrepancy means a
   component is missing from the sum.**
2. **Last-layer structure.** For `h` in layer `27`, `ATT` must be `~0` (no later attention exists)
   and `MLP` must consist only of layer `27`'s own MLP. A decomposition that reports later
   components contributing to a last-layer ablation is mislabelling its own indices.
3. **`OWN` must reproduce `R20`'s `direct`** on the same heads. Different normalisation conventions
   make exact equality unlikely; the Spearman across the `168` band heads is reported and must
   exceed `0.9`, or the two rounds are not measuring the same object.

## The strongest confound, written before the run

**The classes have wildly different membership: `335` other heads against `28` MLPs.** A summed
contribution will favour the larger class even if every member is negligible, and reading that as
*"attention dominates"* would be counting members, not effects.

**Control, in the same iteration:** the **per-member mean** contribution is reported beside every
class sum, and the two are read together. The verdict uses the **sum**, because the sum is what the
margin actually sees — but a class whose sum is large only through membership will show a per-member
mean near zero and that is stated on the page, not left for a reader to derive.

**Second confound: cancellation inside a class.** `335` heads whose contributions cancel would show
a small signed sum and a large activity. Both are computed: the signed sum (what moves the margin)
**and** `SUM |v'_c - v_c|` within the class (how much moved at all). The verdict uses the signed sum;
the ratio of the two is reported as the class's cancellation factor.

**Third confound: the comparator.** Identical to `R20` — the margin's `max over the other three
rooms` can change identity under ablation, which would break additivity. The **clean comparator is
held fixed** throughout so the decomposition stays exactly additive, and the disagreement rate is
reported. `R20` measured that rate at `0.0231` mean, `0.6167` max on one head.

## What each outcome costs me

**`RENORM-DOMINATED`** is the outcome that costs the most and I would find it unwelcome: it would
mean `R20`'s `3.3x` — published two hours ago — is largely a **gain change**, and that every
margin-based effect size in this repository inherits a normalisation artefact nobody separated. It
would not overturn `R20`'s kill of self-repair, which rests on signs and magnitudes, but it would
deflate what the surviving term *is*.

**`ATTENTION-DOMINATED`** would mean removing one head at one position changes *what the model
attends to*, which entangles single-head attribution with routing and makes `I_final` a measurement
of a graph, not of a component.

**`MLP-DOMINATED`** is the least interesting and therefore the one to distrust.

## Boundary

One model, one metric, one task, `I_final` support, `168` band heads, `n = 120` items, final
position only. The decomposition is exact **for a fixed comparator** and is not a causal claim about
any class: attributing a share of the margin change to the MLPs does not establish that the MLPs
*caused* it, only that their writes account for it. Nothing here says which MLP or which head, and
nothing here is about `I_all`.
