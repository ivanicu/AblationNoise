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

---

# Amendment 1 — `MIXED`, and the pre-registration contradicted itself

Appended 2026-07-29. **No threshold above was changed.**

## The registered control could never have passed, and this same file says why

> **Positive control 1:** *"`OWN + ATT + MLP + EMB + NORM` must equal `R10`'s frozen `total(h)`."*
>
> **Third confound:** *"the **clean comparator is held fixed** throughout so the decomposition stays
> exactly additive"* — while `R10` **recomputes** `max over the other three rooms` after every
> ablation.

**Those two sections are incompatible by construction.** Wherever the comparator moves, the two are
different margins, so the control had to fail. It did: `max |total_here - total_r10| = 1.9716`
against a limit of `0.0122`. **A pre-registration that names a confound and then writes a control the
confound must break is a pre-registration that argues with itself, and I did not notice until it
fired.** That is the third registered control in two rounds built on a premise that does not hold.

**The diagnosis is measured, not asserted:**

```
Spearman(|total_here - total_r10|, comparator_flip_rate)                    +0.4831
worst head  L26H07   error 1.97157   flip rate 0.6167   (the band's highest)
44 heads whose comparator NEVER moved:  max error 0.0064726  <= 0.0121759   PASS
```

The `44`-head subgroup is selected on a **covariate registered before the run** — *did the comparator
move at all* — and not on the size of the error. **It is still post hoc, and it is labelled as such
in the code and here.**

What is *not* in doubt is the decomposition itself: `OWN+ATT+MLP+EMB+NORM` reproduces this round's
own measured drop to **`1.7878479721677998e-07`**, and for last-layer heads `ATT` is **exactly `0`**
with no contribution from any later layer — the two structural controls that make the split
meaningful both pass exactly. `OWN` reproduces `R20`'s independent `direct` at Spearman `+0.9068`.

## Registered verdict: `MIXED`

```
class   median share   median |sum|   per member   cancellation
ATT         0.4845        0.055965     0.000167       0.1734       335 members
MLP         0.2341        0.047556     0.001698       0.1392        28 members
NORM        0.1706        0.030222     0.030222          -           1
EMB         0.0000        0.000000     0.000000          -           1
```

No class reaches `0.50`. `ATT` is the largest at `0.4845`; on the `44` comparator-stable heads it
reaches `0.5294`, which is `ATTENTION-DOMINATED` — reported, and **not** promoted to the verdict,
because that population is not the registered one.

## The confound registered before the run decides how this is read

**`ATT` wins the sum by membership.** Its `335` members contribute `0.000167` each; `MLP`'s `28`
contribute `0.001698` each — **`10x` more per member.** So *"attention dominates"* would be counting
members, not effects. The margin sees the sum, and the sum is what the verdict uses; the per-member
column is why the sum must not be read as *"later attention heads are doing the work"*.

**And `83`–`86%` of each class's movement cancels inside the class.** The cancellation factor —
signed sum over sum of absolute contributions — is `0.1734` for `ATT` and `0.1392` for `MLP`. This
was computed as a registered confound control and is the most substantive thing in the round:

> **Removing one head at one position moves a great deal downstream, and almost all of it cancels.
> The indirect term is a small net residue of a large amount of motion.**

## World NORM is dead, and it was the deflationary one

`NORM` carries `0.1706` of the indirect term, not the majority. So `R20`'s `3.3x` is **not** mostly a
gain change — the term survives as a real redistribution of component writes. This round's own
`total/own` ratio is `3.8417x` under its fixed-comparator convention, against `R20`'s `3.3251x`;
both are reported and the difference is the comparator convention, which is the confound above.

`ATT` is entirely from layers **strictly after** the ablated one — `median |ATT from later layers|`
equals `median |ATT|` to `3e-10` — which is what the architecture requires and is a further check
that the indices mean what they say.

## No mechanism is named

This round was registered to attribute and stop. It attributes: roughly half the indirect term rides
on later attention heads, a quarter on MLPs, a sixth on the normalisation gain, and the whole of it
is what survives after `~85%` internal cancellation. **What causes the redistribution is not
established here, and calling it routing, repair, or compensation would be attributing a mechanism to
a datum that does not require it.**

## Boundary

One model, one metric, one task, `I_final`, `168` band heads, `n = 120` items, final position only,
fixed clean comparator. The decomposition is exact for that comparator and is **not** causal:
attributing a share to a class says its writes account for the change, not that the class caused it.
The registered population is all `168` heads; the `44`-head subgroup is post hoc. `EMB` is a measured
residue — `5.4e-08` — which also confirms `o_proj` carries no bias on this architecture.
