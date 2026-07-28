# The defect ledger

> Split out of `README.md` on 2026-07-28 without rewriting.
>
> **The row count is not a result and is no longer quoted as one.** Defect granularity is a
> drafting choice — one root problem can be filed as ten rows, ten wordings as one — so the
> total is not a comparable quantity and says nothing about how rigorous the work is. What the
> ledger is for is the *shape*: which kinds of check fail, and in which direction.

## The defect ledger — the repository's own error record, exhibited rather than asserted

Every defect this project found in itself, each resolved to a commit that `make verify` re-checks
is an ancestor of `HEAD`. Not a table in a README: a hand-written ledger is a self-report.

```bash
python3 validate_defects.py
```

Every runner stamps `sha256` of its own source into the result file it writes, so *"which code
produced this number"* is a query rather than a memory —
[`validate_provenance.py`](validate_provenance.py), also in `make verify`. It is three-valued: a
matching stamp is `CONFIRMED`, a differing one is `STALE`, **no stamp at all is `UNVERIFIED`** and
falls back to git timestamps, which are weaker evidence and are reported as such. The 40 results
that predate the stamp are all `UNVERIFIED`, and git shows **12 of them were produced by code that
has since been edited**.

Downloaded the ZIP rather than cloning? The ancestry check reports **UNVERIFIED** and says so —
it does not fail, and it does not claim the rows are wrong. There is no repository to check
against, which is a fact about your directory and not about the ledger.

```
    PROVENANCE     22      whether the number has a generator at all
    SCOPE          20      which population the claim covers
    CONTROL        18      what the control arm actually holds fixed
    STATISTIC      15      what quantity the number is
    UNCLASSIFIED    4
    INTERVENTION    2      what the operation physically writes / where / when

    found by:  author reading the object 47 · instrument 18 · outside reader 7
               author attacking own detector 6 · author writing the adversary predictions 2
               author writing it up 1 · detector 6 1
```

**Not one of the 82 is a statistics error.** Every one is the same shape: a *label* carried where a
*derivation* was needed — an intervention called gentle that was smaller, a control said to hold one
thing fixed that held two, a ratio of standard deviations called a variance, a number quoted from a
commit message that no code emits.

**7 of 82 were findable only by an outside reader** — `8.5%`. That fraction was 27% at n=22 and
falls as the author keeps finding more, which is the right direction and also a reminder that a
ceiling estimated from a small sample moves. **Every count in this section is now generated from
[`defects.json`](defects.json) by `make headline`** — they were maintained by hand, and a hand-kept
tally on a ledger that grows every session is wrong one commit after it is written.

And the split is not uniform. Cross-tabulating the joint against who found it:

```
joint            by the author   by an instrument   by an outside reader
PROVENANCE            13                9                    0
SCOPE                 16                2                    2
STATISTIC             11                4                    1
CONTROL               12                2                    4
UNCLASSIFIED           4                0                    0
INTERVENTION           1                1                    0
```

**Both halves of the claim this detector suite was built from are now dead — and the same two
`--check` lines killed them.** At n=`37` the build asserted that no instrument had ever caught a
`CONTROL` or a `SCOPE` defect, written that way precisely so it would fail the day either changed.

* **`CONTROL` fell at n=`49`.** The provenance validator fired on its own during a routine gate run,
  and what it revealed was a false-conviction rule **inside itself**.
* **`SCOPE` fell at n=`67`, and again at n=`68`.** [R14](R14_position_vs_binding/)'s pre-registered probe refuted an
  implication its author had left hanging across two steps.

Both times **the expected count was updated and the check was not.** It took `30` further ledger
rows for the instruments to reach the two joints they had never touched, and neither was reached by
being read — **each fired on its own.** That original measurement is what
[`arm_contrast`](detectors/arm_contrast.py) was built from: aimed at the joint the instruments had
never reached, with the real defect eight rounds inherited as its first selftest case.

**An outside reader still holds the lead on both**: `4` `CONTROL` and `2` `SCOPE` against the
instruments' `2` and `2`.

### The taxonomy verdict is **dead as evidence** — measured, not suspected

[Pre-registered](DEFECT_TAXONOMY_PREREGISTRATION.md) before any row was written, because the author
classifying his own defects will group them until a taxonomy appears. `ONE-JOINT-DOMINATES` fires
when any bin reaches `8`. **That is an absolute threshold on a ledger that grows every session, and
this page said so at n=`31` — and then nobody measured how uninformative it had become.**

**Permutation test, labels assigned uniformly at random over the six bins:**

```
n = 22    the verdict fires  12.65% of the time      informative
n = 31                       66.975%                  already mostly inevitable
n = 45                      100.0%
n = 82                      100.0%   (20000 of 20000 random relabelings)
```

> **At n=`82` the verdict carries no information at all.** It was informative at n=`22` and stopped
> discriminating around n=`45`. It is reported here rather than deleted, because **a pre-registered
> gate that stops discriminating is a finding about the gate**, and quietly dropping it is how a
> ledger keeps only the tests that still flatter it.

**And the verdict space has collapsed — which is sharper than the permutation test.** Replaying the
verdict row by row:

```
n =  1  THIRTEEN-ONE-OFFS      n = 12  TAXONOMY-EXISTS       n = 26  ONE-JOINT-DOMINATES
n =  3  AMBIGUOUS              n = 22  AMBIGUOUS                     … frozen for 44 rows
```

**The test worked, and then the ledger grew past it.** `UNCLASSIFIED` never decreases — rows are
never removed — and `TAXONOMY-EXISTS` requires it `≤2`, so **that outcome became permanently
unreachable at n=`22`.** `THIRTEEN-ONE-OFFS` needs `≥5`, and even then the `≥8` branch is tested
first and masks it. **One reachable outcome is not a test**, and `validate_defects.py` now prints
the reachable set on every run so the collapse is stated rather than discovered.

**What replaces it is the distribution, and that *is* informative.** Chi-square `34.118` against a
uniform null gives a permutation `p` of `0.0002` — `4` of `20000`.

```
PROVENANCE 22   SCOPE 20   CONTROL 18   STATISTIC 14   UNCLASSIFIED 4   INTERVENTION 2
                                                        expected 13.5 each
```

**The two *small* bins carry the signal** — `INTERVENTION` at `2` and `UNCLASSIFIED` at `4` — not
the large one the threshold watches. The right question was never *does a bin dominate* but *is the
partition uneven*, and the answer sits at the opposite end of the distribution from where the
threshold was pointed.

**Still self-reported.** The rows are the author's, the bins are the author's, the classification is
the author's. This measures whether the partition is uneven, not whether it is right.

And the three do not split evenly: **two of them are the same unnamed type** — a prediction row
derived from a *world's name* instead of from what the arms physically do, which happened in R7 and
again in R8, in the round written to fix R7. The bin set was missing a sixth joint.

> **The bins were themselves a label-carried-instead-of-derived defect.** They were taken from the
> author's own one-sentence statement of the programme — *intervention, control, statistic, scope* —
> rather than derived from the defects. The taxonomy test caught its own designer, in the design of
> the test. The two rows stay `UNCLASSIFIED`: moving them into a new bin after seeing them is how
> `AMBIGUOUS` becomes `TAXONOMY-EXISTS` without any evidence changing.

