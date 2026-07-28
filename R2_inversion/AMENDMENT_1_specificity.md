# R2 AMENDMENT 1 — the round-invalidating check assumed an inert control that is not inert

Written 2026-07-27, **immediately after the check ran and before any other R2 run**. The
pre-registration is `e60a1c2`; nothing in it is being quietly reinterpreted. The check FAILED as
written and this file states what that failure actually showed.

---

## What the pre-registration said

> **WHAT WOULD MAKE THIS WHOLE ROUND WRONG.** If the prefix-matching score does not identify heads
> whose ablation hurts induction on any model, then there is no known mechanism here and R2 has no
> positive control of its own. That is checked first, on one model, before the full run: **if the
> top-k induction heads do not beat the bottom-k, the round stops and says so.**

## What came back, on qwen2.5-1.5b

```
baseline induction logprob    -0.2089     (the model does induction nearly perfectly)
ablate top-5 induction heads  -4.7281     sign CORRECT, and large
ablate bottom-5               -11.2414    LARGER
```

By the criterion as written: **FAIL**.

## What the failure actually shows, and why it is not the failure that was pre-registered

The pre-registered concern was *"the score does not identify heads whose ablation hurts induction"*.
It does: −4.73 against a baseline of −0.21 is a near-total destruction of induction, in the expected
direction. **The premise of the round survives.**

What broke is the comparator. `bottom-k` was used as an inert control on the unexamined assumption
that the *lowest*-scoring induction heads do approximately nothing. Nothing established that, and
the measurement says the opposite: ablating five arbitrary heads **at every position** costs 11
nats. They are not an inert set; they are five heads that happen to matter enormously for ordinary
next-token prediction, measured with a metric that is ordinary next-token prediction.

**This is R1's own finding one level up.** R1 measured that the effect of ablating a random set is
large; R2 then used a hand-picked set as if it were the zero point. The correct comparator was
always the size-matched RANDOM NULL — the thing R1 exists to supply — and I wrote a cheaper one into
the gate without noticing it was the same mistake.

## The honest cost of this amendment

* The pre-registered stop criterion **failed**, and that is recorded as a failure, not reinterpreted.
* The check's *purpose* — confirm a known mechanism exists before spending compute — is **met**: the
  positive control fires, with the right sign, at 22× the baseline magnitude.
* **The bottom-k arm is withdrawn as a control** and demoted to a reported arm. It measures "five
  low-induction heads", which is a fact about those heads, not a zero point.
* Any later sentence of the form "top-k beats bottom-k" may not be used as evidence of specificity.

## The amended criterion, effective for every R2 run after this commit

```
ROUND PROCEEDS iff, on at least one model:
    sign(d_top) is negative                         (the mechanism's removal hurts the outcome)
  AND d_top clears 2 sd of the SIZE-MATCHED RANDOM NULL, in the correct direction
```

The null is 30 draws of K heads from the same pool, ablated the same way, exactly as R1 defines it.
The `bottom-k` arm still runs and is still reported, because "the lowest-scoring heads cost 11 nats"
is a genuinely useful number about how blunt all-position ablation is — but it decides nothing.

## What this predicts about the round's main question, stated now so it is not a post-hoc read

If ablating five arbitrary heads at every position costs 11 nats against a 0.21 baseline, then the
random null for this metric is enormous, and **most known-mechanism effects will fail to clear it**.
That would make R2's *second* quantity — how often a correctly-signed effect still fails to clear
its own floor — the round's actual result, and the inversion question may turn out to be
unanswerable on this metric because nothing clears the floor at all.

If that happens it is a real finding about all-position ablation, not a null result, and the
gate above will return NOT MET rather than being widened to accommodate it.
