# R9 — the floor at every layer, because R1's two arms differ in depth as well as in kind

[R1](../R1_noise_floor/) reports a ratio: the floor of a **late** band of layers over the floor of
an **early** sham band. That number is the repository's opening claim. It has an obvious rival
explanation that R1 could not see from inside itself —

> **the floor might simply grow with depth.** Then the ratio is a fact about *where the two pools
> sit in the stack*, and nothing about the heads inside them.

R9 measures the floor at **every layer** so the curve can be read instead of inferred.

```bash
python3 R9_depth_profile/run.py --model <hf-path> --tag <name>
```

---

## The curve — 4 models, 30 draws per layer, shared vocabulary

`floor = sd(null draws) / |baseline margin|`, computed independently at each layer.

```
model              quietest layer      noisiest layer    whole-stack   largest adjacent   band/sham   rho
internlm2-1.8b     L8   0.0161         L0   0.1296          8.1x       L0->L1    4.9x       1.08x    0.510
phi-3.5-mini       L1   0.0004         L19  0.0422         96.2x       L9->L10   4.8x       6.35x    0.682
qwen2.5-1.5b       L1   0.0073         L18  0.1175         16.1x       L23->L24  5.1x       4.02x    0.732
qwen2.5-3b         L6   0.0018         L26  0.1104         62.0x       L0->L1   15.2x       4.56x    0.557
```

**Spearman rho between layer index and floor is positive on 4 of 4.** The rival explanation is
real: the floor does grow with depth, so R1's band and sham arms differ in *where they sit* as well
as in what they contain. R1's ratio is therefore **not** clean evidence that late heads are
individually noisier than early ones — a claim R1 never made, and now cannot.

## The scope error this round produced, and the correction

Two pages in this repository said *"neighbouring layers differ **tenfold**"*. They were reading the
**whole-stack** column and writing the **adjacent-layer** label.

```
whole-stack spread        8.1x    96.2x    16.1x    62.0x     -> "tenfold" holds on 3 of 4
largest ADJACENT jump     4.9x     4.8x     5.1x    15.2x     -> "tenfold" holds on 1 of 4,
                                                                 and that one is L0->L1
```

The one adjacent pair that clears ten is `qwen2.5-3b`'s `L0->L1` — the **embedding boundary**, not
a mid-stack neighbour. Both pages are corrected in place rather than deleted, because the
conclusions that cited them never needed the stronger version.

`headline.py` now emits `stack_spread` and `largest_adjacent_ratio` as **separate fields**, and
`--check` asserts **both** ranges. Asserting only one would let the two merge again the next time
either page is edited.

## Its own gate is REFUSED — the estimator failed twice, in two different directions

The pre-registered gate asked whether the band's floor **exceeds what depth alone predicts**. It
built that prediction by fitting the sham half's trend and extrapolating to the band's depth.

> **The band is the upper half of the stack.** There is no data at the band's depth except the
> band. Every "predict the band from the rest" is extrapolation, not interpolation, and the
> pre-registration did not notice because it specified the *gate* and left the *estimator* free.

What the two admissible estimators returned:

| form | outcome |
|---|---|
| linear | **predicted standard deviation is negative on 2 of 4 models** — `internlm2-1.8b` and `qwen2.5-3b`, so the excess is `nan` |
| log | the same quantity spanned four orders of magnitude across models |

A negative standard deviation is not a marginal result; it is the estimator announcing it is being
used outside its support. **The gate is `UNVERIFIED`** — the check was unfit, which is not an
acquittal for either world. The shipped verdict strings (`AMBIGUOUS` on three models,
`DEPTH-EXPLAINS-IT` on one) are emitted by `make headline` **so the refusal itself can be checked**,
and are not used anywhere as a conclusion.

[R10](../R10_exhaustive/) is the round that answers what R9 could not, by a route with no estimator
in it at all: at `k=1` inside a single layer there is nothing to sample, so every head is ablated
once and the layer's floor is **exact**.

## What this round does NOT conclude

- **Nothing about whether the band is exceptional.** That was the gate, and the gate is refused.
- **Shared vocabulary**, so these floors are not comparable to the eight published effects, which
  live in the original vocabulary — a 1.7× difference established in
  [R1's Amendment 2](../R1_noise_floor/). R10 exists partly because this round could not be reused.
- **30 draws per layer**, which is sampling: at `k=1` a layer has only `n_heads` distinct
  single-head ablations, so 30 draws over 12 or 16 objects resample. The spread reported here
  therefore carries sampling noise that R10's exhaustive measurement does not.
