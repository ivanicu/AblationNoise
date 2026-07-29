<!-- unbacked-ok: 0.0006 3e-05 0.00216 0.0028 0.0722 0.0077
 -- THE REVIEWER'S FIGURES, NOT YET REPRODUCED HERE. Six numbers in this file were measured by the
 independent code review that produced the rule, with its own implementation, and no generator in this
 repository emits them yet. They are marked rather than quoted as backed, because a number taken on
 trust from another agent is exactly the thing this repository refuses everywhere else -- twelve agents
 agreeing is one hallucination twelve times. The replacement implementation reproduces them next; when
 it does, this marker shrinks. Anything still listed here is still hearsay. -->
# Amendment 1 — the confound control was collinear with the thing it controlled

Registered 2026-07-29 by transcription from an independent code review, before the replacement pool
was computed. Committed alone. **The rule, the pool and the threshold below are the reviewer's, not
the author's.**

## What was wrong

`attack_partition.py` ranked the KV partition against two references and claimed the second ruled out
head-index locality: every balanced two-way partition (`462` / `6435`), and **every contiguous split
point** (`11` / `15`).

The second pool is unfit, and unfit in the one direction that mattered.

- Its members have shapes `(1,11), (2,10), … (11,1)`. **Exactly one is balanced — and that one IS the
  KV partition.** In a layer with two equal KV groups, "balanced contiguous split" has a single
  member. Contiguity and KV grouping are therefore *perfectly collinear* inside that pool.
- The shapes are not comparable: the measured null `sd` of the unbalanced members is `0.148` against
  `0.104` for balanced ones at `n=12`, `42%` larger. So `contiguous_max` (`5.597`, which exceeds the
  KV value `5.173` in `3b|I_all|abs`) is not a like-for-like reference at all.

`PROPERTY` KV grouping structures the effects · `PROXY` the KV partition outranks other contiguous
splits · `DIRECTION` KV grouping implies a high rank; **the converse is untestable with this pool.**
The prior claim — *"contiguity predicts a high rank among the contiguous splits and predicts nothing
about being the global argmax"* — is **UNVERIFIED, not an acquittal.**

## The replacement pool, the reviewer's code verbatim

Cyclic blocks of `n/2`: `6` partitions for `n=12`, `8` for `n=16`. Every member is shape-matched to the
KV partition and every member is contiguous on the ring, so the pool isolates *which* contiguous
half-layer rather than *whether* the split is contiguous.

```python
def cyclic_blocks(n):                 # 6 partitions for n=12, 8 for n=16
    seen = {}
    for st in range(n):
        c = {(st + j) % n for j in range(n // 2)}
        lab = tuple(1 if i in c else 0 for i in range(n))
        seen[lab if lab[0] == 1 else tuple(1 - x for x in lab)] = st
    return [list(l) for l in seen]
```

## The registered rule, fixed before looking

**KV must be the argmax of the cyclic pool in all four cells of the primary transform.** Measured
joint base rate `0.00060`. Per-cell floor is `1/6` and `1/8`, so **no single cell can carry the
finding** — that is the property the old pool lacked.

**The primary transform is `abs`, and it was chosen after seeing both.** That is stated rather than
hidden: the code computes eight cells, four on signed effects and four on magnitudes, and no
pre-registration ever fixed which. The penalty is paid in the number quoted — **the honest family is
`8` and the joint rate is `0.00010`, not `0.00003`.** Any future statement of this finding carries the
eight-cell rate.

## Why this rule can fail in both directions, and already does

The reviewer computed the replacement before registering it and reported the outcome as part of the
rule, so the failure mode is not hypothetical: KV is the argmax of the rotations in
`1.5b|I_final|abs`, `1.5b|I_all|abs` and `3b|I_final|abs`, and **loses to a rotation in
`3b|I_all|abs`** — where that rotation, `0000000111111110` (heads `{15, 0..6}`), is also the global
argmax of all `6435` and is a one-step rotation of the KV block. So the registered "all four" rule is
**not** satisfied, and this amendment exists to record that before the code is rerun rather than after.

## Two corrections to numbers already committed

- `3b|I_all|abs`: **`2` of `6435`** balanced partitions beat KV, not `1`. Rank `0.9996892 = 1 −
  2/6435`.
- The raw `η²` values were quoted in a commit body in the form the runner's own docstring forbids.
  For `3b`, `0.0667` of `0.1317` is pure null bias; only the **excess** is the effect size.

## What survived the same review, unchanged

All eight `η²` / excess / `p` values and all eight balanced-pool ranks reproduce exactly under an
independently written implementation. `E[η²] = (k−1)/(n−1)` was verified exact even for heavy tails
and unbalanced groups (`200,000` permutations, `t(2)` data). "Argmax of all `462`" is an exact test at
`p = 1/462 = 0.00216`, confirmed by simulation at `0.00205`–`0.00280`. And the effect is **not** "where
the biggest head sits": it survives dropping each layer's top head (`p = 0.0002 / 0.0722 / 0.0002 /
0.0012`) and survives a within-layer rank transform (`p = 0.0002 / 0.0077 / 0.0002 / 0.0002`). It is a
group-level property of the whole ordering.
