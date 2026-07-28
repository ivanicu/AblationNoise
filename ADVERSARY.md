<!-- unbacked-ok: 17.2 24.3 41 500 700 35 -- the detector's own false-pass rate, which cannot
 enter the reference set without infinite recursion (measuring it requires building the set).
 17.2% was measured 2026-07-28 at ~500 reference values, 24.3% the same day at >700. The LIVE
 figure is printed by every `make verify` run, so these two are dated history, not the current
 value -- read the gate, not this page. -->

# What an adversary will overturn — written before one runs

2026-07-28. **No independent challenger has reviewed this repository.** Every claim in it is
`[unchallenged]`, which is not the same word as *clean*, and the difference is the point: a reviewer
sampled from the same weights that wrote the material can only attack what its author already
anticipated — which is exactly why those parts read as fluent.

So this file does the only honest thing available: **it predicts, in advance and in rank order, what
a hostile clean-context reader will find.** When one eventually runs, its findings score this list,
and *that* number — how well the author predicted his own blind spots — is worth more than any
individual verdict.

**How to score it.** For each row: did the adversary raise it? Did it land at the predicted
severity? A row raised and landing *harder* than predicted is a miss. A row not raised at all is
also a miss — it means effort was spent defending something nobody attacks.

---

## The predictions

### A1 · "Eight published effects" oversells the population — `LANDS, and I expect it to land hard`

> The set is E132b's eight heads: **five were read-head *candidates*, one (`L22H7`) an independently
> proven copy head**, two unlabelled. The front page calls them "eight published single-head
> effects" and R1's own README calls the candidate framing a strength.

**The attack:** a candidate is a hypothesis, not a result. Finding that five hypotheses fail to clear
a noise floor is close to tautological — R1's own set-level data says the READ set sits at the
`46.7`th percentile of the null, i.e. *there was nothing there to find*. **The number of
independently established mechanisms shown to be inside the floor is `1`, not `8`.**

**My assessment: this is correct and the framing should change.** The one that matters is `L22H7`,
and it carries the whole claim by itself. I predict the adversary states it more sharply than this
paragraph does.

> **ACTED ON, same day, before any adversary ran.** The front page no longer says "eight published
> effects"; it leads with the one established mechanism. **This row can no longer be scored** — a
> self-corrected prediction is not a tested one, and the only evidence it was written first is the
> commit order. Recorded here rather than deleted, because a prediction file that quietly drops the
> rows its author fixed is a file that always scores well.

### A2 · The whole repository is one synthetic task — `LANDS`

One 4-way binding task, one prompt template, `n=120` items, one readout (margin), four models of
which one supplies every headline number. Individual pages state the scope; **the headline sentence
does not.**

**Prediction:** the adversary will say the title claims something about ablation and the evidence is
about *this task*. I agree, and I do not currently have a second task.

### A3 · `k=1` is the wrong granularity, and the repository's own data says so — `LANDS, and this is the one I would rank first if I were attacking`

The front page already concedes the `k=1` regime is **sub-behavioural**: the floor is `9.9%` of the
distance to a different answer, the largest effect `10.4%`. And R1's set-level result shows the
**COPY circuit at the `0.0`th percentile of the k=5 null** — a real, enormous, localised effect.

**The attack:** if ablating the actual circuit produces an unmistakable effect and ablating one of
its heads does not, the finding is *"single heads are the wrong unit"*, not *"published effects are
noise"*. The repository has the data for the stronger, more useful claim and leads with the weaker,
more provocative one.

**My assessment: I think this substantially lands**, and the counter — that single-head effects
*are* what gets published, so measuring their floor is the point — is a reason the work matters, not
a reason the framing is right.

> **ACTED ON, same day.** The front page now leads with *"the single head is the wrong unit"* and
> puts the `k=5` circuit result (`0.0`th percentile, `−1.4279` against a `4.477` margin) beside the
> single-head number instead of three screens below it. **Also unscoreable now**, for the same
> reason as A1.

### A4 · `2 × sd` is a normal-distribution threshold on a visibly non-normal null — `PARTLY LANDS`

`L22`'s twelve heads: `+0.3977, −0.3379, −0.2214, +0.2049, −0.1317, +0.0751, −0.0688, −0.0260,
−0.0256, −0.0199, +0.0194, +0.0099`. Heavy-tailed, asymmetric, `n=12`.

**Prediction:** the adversary proposes an empirical percentile instead. **I do not know whether the
count changes** — that check is not in the repository and should be. Predicted severity: medium,
because R1 *already* reports percentiles at the set level and the two conventions coexist unreconciled.

> **RESOLVED 2026-07-28 — the first row in this file to be settled, and it scores me BADLY.**
> The count does **not** change: leave-one-out, each head judged by a null excluding it, still `9`.
> The *interpretation* breaks instead. Excess kurtosis is `+7.43`, and beyond `2 × sd` a normal
> gives `7.6` of `168` while a Laplace gives `9.9` — observed `9`. **So "nine heads clear the floor"
> is the tail a heavy-tailed distribution hands you for free**, and the front-page inference it
> carried (*"so single-head ablation resolves effects here perfectly well"*) never followed.
> **Predicted severity medium; actual severity invalidated a front-page inference.** Under-severe.

### A5 · Two floor definitions still coexist — `LANDS, narrowly`

R9 emits `floor = sd/|margin|`; R10 and R1 use `2×sd`. R5 was already caught by exactly this and
regenerated its table under both. **Prediction: the adversary finds at least one place where the two
are still mixed within a single comparison.** I have not found one, which is weak evidence of absence
given that I am the person who wrote both.

### A6 · Zero-ablation is off-manifold and the repo cannot resolve it — `RAISED, ALREADY CONCEDED`

R6 returned undecidable, R7 was one family short, R8's separating column was inadmissible
(`randdir`'s positive control sign-inverts). **Prediction: raised; no new information.** If the
adversary shows the floor *reverses* under an on-manifold intervention, that is a genuine kill and I
rate it unlikely but not negligible.

### A7 · `0 unbacked` is weaker than it sounds, **and it gets weaker every time the project grows** — `LANDS, and writing this row found the sharper version`

`make verify` checks that each prose number appears in a reference set of generated values. The
detector measures its own false-pass rate: how often a *random* number of the shape this repository
writes is "backed" by coincidence.

**Predicting this attack is what caught the real problem.** The rate quoted here was `17.2%`,
measured at a reference set of about `500`. One session of additions later the set is over `700` and
the same rate is `24.3%` — **a 41% relative increase in false passes, caused entirely by the
repository succeeding.** Every generator added to strengthen the gate weakens this detector, and
nothing was watching.

It is now measured on **every** `make verify` run and printed under the file table, with a ceiling
that fails the build if it is breached. The ceiling was chosen knowing the present value, so it is
**not** a pre-registration and is not claimed as one — its job is to bound future growth.

**Prediction:** the adversary quotes the false-pass rate back. **It is correct**, and the honest
reading of a clean row is *(1 − that rate)* per number rather than a guarantee.

### A8 · The defect ledger is self-reported — `LANDS`

`60` rows, `31` of them found by the author reading the object, classified by the author, against
bins the author pre-registered. The taxonomy test caught its own designer once; **that is one check, not
independence.** `7` rows came from an outside reader. The cross-tab used to show that **no
instrument had ever caught a `CONTROL` or `SCOPE` defect**; at n=`60` an instrument has caught its
first `CONTROL` one — a false-conviction rule inside the provenance validator, which the validator
surfaced itself. **`SCOPE` is still `0` from instruments against `2` from an outside reader.**

**Prediction:** the adversary says the ledger measures *what the author noticed*, not *what is
there*, and the `11.7%` outside-reader fraction is a floor on the true rate, not an estimate. Correct.

---

## What I predict the adversary will NOT find

Stated so the list can be wrong in both directions:

* **A fabricated or unreproducible number.** After the blockquote exemption was removed, `625` prose
  numbers across `11` files are checked against generated output, and the three that survive
  unbacked are listed by value with a reason in each file's header.
* **A hook that does not do what it claims.** Verified exact on four families, `92` heads, three
  module names, one fused-QKV architecture, residual `5.14e-07` to `7.41e-06`.
* **A verdict quoted without its refusal.** R4, R9 and R10's gates are all refused in place, with
  their numbers still emitted so the refusal itself can be checked.

**If the adversary finds one of these three, the failure is worse than any row above** — it means the
part of the process I trust most is the part that was broken.

---

## The prediction I am least confident in

**That A3 is the strongest attack.** I rank it first because it is the one I cannot answer, which is
also exactly the bias this file exists to expose: an author's sense of *"the attack I cannot answer"*
is drawn from the same distribution as the work. The adversary may well lead with something not on
this page at all — and **a finding absent from this list is the most valuable thing it can return.**
