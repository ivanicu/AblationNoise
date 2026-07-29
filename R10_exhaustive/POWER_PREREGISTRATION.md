# Pre-registration — what enrichment could the central null actually have detected?

Written 2026-07-28, **before the statistic was computed**, committed alone so git ordering rather than
my word establishes that the thresholds preceded the numbers.

## The claim under attack is this repository's central one

> *"The eight are NOT enriched under matched-layer randomization"* — `p = 0.8069 / 0.6917`
> distinct-per-layer, and the signed variants.

An independent adversarial reviewer returned this, `CONFIRMED`, on 2026-07-28:

> The offered positive control — *"the actual top-`8` by `|centred|` is reached by only `0` of
> `50000` matched sets, so the test can separate"* — **is an arithmetic identity, not a measurement.**
> `top8` is by construction the argmax of the test statistic over all 8-head subsets of the band, and
> every null draw is an 8-head subset of the same band. `T(null) <= T(top8)` with probability `1`.

It is right. **This repository's own standing rule is that a null is inadmissible until the
instrument has passed a positive control**, so the central negative claim is currently `UNVERIFIED` —
not an acquittal, and not overturned either.

## What a real positive control is

Not *"can the test find the maximum"*. **Plant an enrichment of known size and measure the detection
rate.** That is a power curve, and it converts the null from a bare `p` into a statement with a
resolution attached.

## Design

Population: the `168` band heads `L14`–`L27` of `qwen2.5-1.5b`, centred effects `|x − mu_band|`.

```
for each planted enrichment delta (in units of the band sd):
    draw a matched-layer 8-head set S at random
    add delta * sd_band to |centred| for the heads in S
    run the SAME matched-layer randomization test the repository uses
    record whether it fires at alpha = 0.05
detection rate over N_PLANT independent plantings = POWER at that delta
```

`delta` swept over `0, 0.25, 0.5, 1, 2, 4`. `N_PLANT = 300`, `N_NULL = 2000` per planting,
`alpha = 0.05`, seed `20260728`. The randomization is **matched-layer distinct-per-layer**, identical
to the one whose `p` is being interpreted — a power curve for a *different* test would answer a
different question.

## Positive controls on the power analysis itself

1. **At `delta = 0` the detection rate must be about `alpha = 0.05`.** A power routine that fires
   more often than nominal on unplanted data is measuring its own bias, and every number below it
   would be uninterpretable. **This is the calibration check and it must pass before any other row is
   read.**
2. **At large `delta` the detection rate must approach `1`.** A routine that cannot detect a
   four-sigma enrichment is not a test.
3. **The planted sets use the same matched-layer construction as the null**, so the plant cannot be
   detected merely by having an unusual layer profile.

## Registered thresholds

| quantity | definition |
|---|---|
| **MDE80** | the smallest `delta` reaching `>= 0.80` detection, by interpolation on the swept grid |
| **observed enrichment of the eight** | `mean |centred| over the eight − mean |centred| over the band`, in the same sd units |

| verdict | rule |
|---|---|
| **NULL IS INFORMATIVE** | observed enrichment of the eight `>= MDE80` — the test could have seen an effect of the size actually present, and did not |
| **NULL IS UNDERPOWERED** | observed enrichment `< MDE80` — the test could **not** have detected what is there, and `p = 0.8069` says nothing about enrichment |
| **UNVERIFIED** | calibration control 1 fails |

**`UNDERPOWERED` is the outcome that costs me the most and it is the one I expect**, because the
eight sit at `0.07`–`1.06×` of the floor and the floor is `2` sd wide by construction.

## What each outcome changes

**If `UNDERPOWERED`:** the front page's *"not enriched"* must be restated as *"no enrichment of
detectable size, where detectable means `>= MDE80` sd"* — a bound, not an absence. Every downstream
sentence resting on the eight not being special inherits that bound. **This is the second time the
same repair has been needed: `resolution_limit()` already found the per-head test has no resolution
beyond ordering, and the set-level test was explicitly defended at the time as the one that *does*
have resolution. That defence is what is being tested here.**

**If `INFORMATIVE`:** the central null survives its first real positive control and stops being
`UNVERIFIED`.

## Boundary

One model, one metric, one task, `I_final`, `168` band heads, `n = 8` in the tested set. A power
curve is computed under an **additive** enrichment on the centred magnitude; a multiplicative or
sparse enrichment would give a different MDE and is not tested. Nothing here is about `I_all`.

---

# Amendment 1 — the outcome, and a defect in the registered rule itself

Appended 2026-07-28 after running `enrichment_power()`. **The thresholds above are unchanged and the
verdict they produce is honoured**, but running them exposed that one of them was badly written.

## Calibration gate: PASSES

```
detection rate at delta = 0     0.0433      nominal alpha  0.05
```

The routine does not fire more often than nominal on unplanted data, so every other row is readable.

## The power curve

```
planted enrichment (band sd)   0.00    0.25    0.50    1.00    2.00    4.00
detection rate                 .0433   .1333   .3533   .8933   1.000   1.000

MDE80 = 0.9136 sd  =  0.2225 in margin units      (band sd = 0.2435)
observed enrichment of the eight = -0.1226 sd  =  -0.0299 in margin units
```

Both edge controls hold: it approaches `alpha` at zero and saturates at `1` by `2` sd. **The
instrument has real resolution — it is not blind.**

## Registered verdict: `NULL IS UNDERPOWERED` — and the rule that produced it is wrong

The rule was *"observed enrichment `>= MDE80` → informative, else underpowered"*. Observed is
`-0.1226`, so it fires `UNDERPOWERED`.

**That rule asks the wrong question, and it is this repository's own named failure class — a claim
whose test is not its own statement — committed inside a pre-registration.** For a *null* claim, the
relevant question is never *"is the observed effect large enough to be detected"* (when the claim is
absence, the observed effect is near zero **by hypothesis**, so the rule fires `UNDERPOWERED`
whatever the test's true resolution). The relevant question is *"what magnitude of enrichment can be
excluded"*. The rule I wrote could not return `INFORMATIVE` for any true null. **It was a check that
could only fail.**

Recorded rather than quietly re-specified, because a pre-registration that repairs itself after
seeing the data is not a pre-registration.

## What the numbers actually license

> **A set-level enrichment of `0.9136` sd or more would have been detected at a rate of `0.8933`. What
> was observed is `-0.1226` sd.**

That is a **bounded absence**, and it is strictly more than the bare `p = 0.8069` said. The adversary
was right that the old positive control was void; the replacement shows the test is calibrated and
has resolution, so the central claim moves:

```
before   "the eight are not enriched", p = 0.8069, positive control VOID       -> UNVERIFIED
after    enrichments >= 0.9136 sd excluded at `0.80` power; observed -0.1226 sd   -> BOUNDED ABSENCE
```

**And the bound is what must now be quoted.** Enrichments below `0.9136` sd are not excluded by this
test and never were — the front page said *"not enriched"* with no such qualifier for the whole life
of the claim.

## Boundary

One model, one metric, one task, `I_final`, `168` band heads, `n = 8` in the tested set, additive
enrichment on the centred magnitude. A multiplicative or sparse enrichment has a different `MDE` and
is not tested. `300` plantings gives the detection rates a standard error near `0.02`, so `0.8933` is
not distinguishable from `0.87` or `0.92` and `MDE80` is an interpolation on a coarse grid.
