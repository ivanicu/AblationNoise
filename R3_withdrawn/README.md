# R3 — WITHDRAWN. Its premise was false, and the project's own database says so.

Written 2026-07-27, **before any R3 compute was spent**. The pre-registration is `b54e41c`.

## What R3 asserted

> "That −0.14 **is the entire specificity argument**."

## What is actually recorded

`x_vstruct3.detail.profile` in the persona_forensics claim graph:

```
u_L16     0.98     <- the claim
random   -0.02
meandisp -0.04
op12_L12  0.53     <- a structured control that PARTIALLY rescues
op20_L20 -0.06
```

**Four control directions, three of them structured, and one of them half-works.** The specificity
argument is not one random draw. It is a profile across adversarial controls, and it includes a
control the project reported as partially succeeding — which is the strongest kind to publish and
the easiest to omit.

## How I got it wrong

I read `x_opnec.detail.control_effect = -0.14`, saw `control_kind: "random_dir"`, opened
`llama_necessity_rand.py`, found it loading a single saved direction, and generalised from one field
and one script to "the entire specificity argument". The other controls are stored on *different
nodes*, which a query for the claim's own supporting cut does not return.

Door ①, and the specific form is the one this project has a memory for: **a label is not a
description.** `control_effect` is a field name, not an inventory of the controls.

## What it nearly cost

A multi-hour 7B generate-and-judge sweep across N random directions. High-dimensional random
directions concentrate, so it would very likely have come back tight — and I would have reported
"the n=1 control was adequate" as a vindication of something that was never in doubt, having spent
a night of GPU on it.

## The cheap check that would have prevented it, now the rule

**Before critiquing a claim's controls, enumerate ALL of them** — every node whose detail mentions
the claim, not the one field named `control_*` on the cut that supports it:

```sql
SELECT id, detail FROM node WHERE kind='cut' AND detail::text ILIKE '%<claim's quantity>%';
```

One query. It returns the vstruct profile immediately.

## What survives

Exactly one narrow question, and it is not worth a night of GPU on its own: the `random` arm is
still a single draw at −0.02. Given three structured controls already carry the specificity
argument, measuring the random arm's spread would refine a number that is not load-bearing.

**R3 is withdrawn rather than re-scoped-to-fit.** The next round will be chosen against the current
state of the evidence, not against a target I had already committed to.
