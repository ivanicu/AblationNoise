# Pre-registration — is the unexplained 85% a fact about the MEASUREMENT or about the SYSTEM?

Written 2026-07-28, **before the statistic was computed**, committed alone so git ordering rather than
my word establishes that the thresholds preceded the numbers.

## The claim this attacks is my own newest one

`mechanism()` + `alignment` left **`0.8484` of the rank ordering unexplained** by three static
predictors — magnitude, informativeness, readout reach — and I wrote:

> *"What remains is not a property of the head — it is a property of what the rest of the network
> does when the head is gone."*

**That sentence has an untested rival**, and it is the deflationary one.

| | |
|---|---|
| **World S — the residual is the SYSTEM** | the unexplained variation is the network's response to losing a component, so it should be equally unexplained under **any** knockout of that component. |
| **World M — the residual is the MEASUREMENT** | `I_final` removes a head's write **at one token position only**. Which downstream paths happen to read that one position is idiosyncratic routing, so much of the residual is an artefact of the single-position intervention. Then a **whole-sequence** knockout should be substantially more predictable from static properties. |

Under **M**, part of the residual is not about the network at all, and every `I_final` result in this
repository inherits that.

## The test, on data already frozen

`R18_all_positions` holds `I_all` — the same `336` heads, same model, same items, knocked out at
**every** position. Re-run the identical three-predictor analysis with `I_all` as the effect vector.

```
unexplained_3predictor(I_final)   =  0.8484     (measured)
unexplained_3predictor(I_all)     =  ?
```

## The strongest confound, written before the run, and it is serious

**Two of the three predictors are position-matched to `I_final` and NOT to `I_all`.** `R6`'s
diagnostic measured `mean_norm` and `displacement_ratio` from activations **at the final position**.
A worse fit for `I_all` could therefore be pure measurement mismatch rather than anything about the
system.

**Control, in the same iteration:** `align` is computed from **weights only** and is
position-independent, so `partial(|eff|, align | norm)` is the one predictor that is fairly matched
across arms. **The verdict uses the alignment partial; the other two are reported with the mismatch
stated.** This is the whole reason the alignment predictor is worth having here.

Depth is handled as before: everything pooled **and** within-layer, within-layer decides.

## Registered thresholds

Population: `168` band heads `L14`–`L27`, `qwen2.5-1.5b`. Effect = `|x − mu_arm|`, centred **within
each arm** because the arms have different means and a shared centre would import one arm's offset
into the other.

| verdict | rule |
|---|---|
| **RESIDUAL IS SYSTEMIC** | `\|unexplained(I_all) − unexplained(I_final)\| <= 0.10` |
| **RESIDUAL IS PARTLY MEASUREMENT** | `unexplained(I_all) < unexplained(I_final) − 0.10` |
| **RESIDUAL IS WORSE UNDER I_all** | `unexplained(I_all) > unexplained(I_final) + 0.10` |

Secondary, and the one the confound makes trustworthy: the **alignment** partial in each arm, with a
depth-preserving permutation null, `N_PERM = 20000`, seed `20260728`.

## Positive controls

1. **The arms must not be the same vector.** `Spearman(|eff_final|, |eff_all|)` is reported; `R18`
   already measured the raw transfer at `+0.6230`, so a value near `1` would mean the arms were
   mis-loaded and the comparison is void.
2. **The predictors must be identical across arms** — same `168` keys, same order. Asserted.
3. **`I_final` must reproduce `0.8484`** when run through the arm-generalised code path. If the
   refactor moves the number that was already published, the refactor is the finding.

## What each outcome costs me

**SYSTEMIC:** the sentence stands, and the case for compensation strengthens because the residual
survives a change of intervention support.

**PARTLY MEASUREMENT:** I must retract *"what remains is a property of the network"* and replace it
with *"part of what remains is a property of knocking out one position"* — which would also mean this
repository's central object, `I_final`, carries an irreducible idiosyncratic component that no
static property can ever explain. **That is the unwelcome branch and it is why this is worth running.**

## Boundary

One model, one metric, one task, `168` band heads, `n = 12` per layer. `R18`'s `I_all` and `R10`'s
`I_final` share an item set, so the two effect vectors are paired; the *predictors* are not
position-matched to `I_all`, which is stated above and is the reason the verdict rests on alignment.
