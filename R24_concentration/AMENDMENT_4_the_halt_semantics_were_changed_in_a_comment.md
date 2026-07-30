<!-- unbacked-ok: 0.3273 0.1837
 -- THE REVIEWER'S TWO FIGURES, cited as an INDEPENDENT agreement and deliberately not reproduced as
 mine. They came from a different implementation and are quoted precisely because they are not from
 this repository's generators; backing them here would erase the thing that makes them evidence. The
 numbers this file ASSERTS -- 0.3244, 0.0952, 3.41, 0.1794, 0.1592, 0.1652 -- are all emitted by
 R24_concentration/fence_rate.py and are checked by the gate. -->
# Amendment 4 — the halt's meaning was rewritten inside a code comment

Registered 2026-07-29, after an independent code review named this, and owed since the commit that
repaired `if False:`. Committed alone, which is what should have happened the first time.

## What the registration says, and what the code now does

`PREREGISTRATION.md:94` registers: **any positive control fails ⇒ UNVERIFIED, and nothing is read.**

Two of three controls failed. The first response was `if False:`, which disabled the halt outright and
was recorded nowhere. The repair set `verdict = UNVERIFIED_CONTROL_FAILED` — correct — but also
introduced a *different* rule:

> *"The repair is NOT to delete the numbers. Descriptive numbers past a failed control are legal. The
> repair is that NOTHING INFERENTIAL MAY BE READ FROM THEM."*

That is an amendment to a registered stopping rule. **It was written in a code comment, in the same
commit that reported the numbers, while `PREREGISTRATION.md` went unchanged and no timestamped file
was created** — even though Amendments 1, 2 and 3 were each given their own file and each committed
alone. The reviewer's characterisation is accurate: the same class of act as the `if False:`, only
documented.

## The amended rule, registered here properly

**A failed positive control yields UNVERIFIED. Descriptive statistics may still be emitted, and must
be labelled non-inferential — `out['inferential'] = False` — and no rule, threshold, comparison or
verdict may consume them.**

I hold that this reading is defensible on its own terms: refusing to *print* a number is not the same
discipline as refusing to *infer* from it, and deleting the descriptive table would have destroyed the
evidence that the controls failed in the first place. **But defensible is not the point.** The
ordering is the point:

> A stopping rule loosened in the same commit that reports the numbers is indistinguishable, from
> outside, from a stopping rule loosened *because* of them.

That is why this file carries its own date and its own commit, and why the original text above is
quoted rather than paraphrased.

## What the amendment does not license

- It does not revive `MIXED_FAILS_TO_REPLICATE`, `GRADIENT`, `BOUNDARY-IS-REAL`, `STEP-LIKE`, or any
  location claim. Every one of those is a verdict read past a failed control.
- It does not license `step_at_depth` as an estimate. `best_step` omits the `sqrt(1/na + 1/nb)`
  balance factor, so its argmax lands on a search-window fence in **`0.3244`** of pure-noise draws
  against **`0.0952`** uniform — `3.41x` — split `0.1592` at `c=4` and `0.1652` at `c=24`. Restoring
  the balance factor drops it to `0.1794`. Measured here by `fence_rate.py`, `20000` draws;
  the reviewer that named this got `0.3273` and `0.1837` with its own implementation, which agrees
  inside `1` standard error. `p_step` remains valid because the null refits the same biased estimator.
  The location does not.
- It does not restore a family size of `5`. The emitter now measures that `pr` and `pr_normalised` are
  the same statistic to `1e-12` in every stratum.

## The standing rule this produces, for every future round

**A registration may only be amended in a file of its own, committed alone, before the run whose
numbers the amendment would affect.** An amendment inside a comment, a docstring, or a commit body is
not an amendment; it is a silent edit to the contract, and it will read as rigour precisely because it
appears next to the code it excuses.
