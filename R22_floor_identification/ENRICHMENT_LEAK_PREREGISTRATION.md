<!-- unbacked-ok: 1.3333
 -- arithmetic shown inline on the layer multiset, computed here before any run and therefore
 emitted by nothing yet; the tool below emits `expected_overlap` and this file's Amendment will
 quote that. Kept as written so the prediction is dated to the registration. -->
# Pre-registration — three leaks, three corrections, and every one of them made my own claim stronger

Written 2026-07-29, **before the corrected `p` was computed**, committed alone so git ordering rather
than my word establishes that the direction was predicted before it was measured.

## The pattern I am about to test on myself

Today, three separate leakage corrections have landed:

```
D177  two of the eight are inside the floor's reference       leave-out -> L16H3 clears by MORE
D178  the floor is a 30-draw sample of an available census    census    -> the count goes 7 -> 8
```

**Both moved in the deflationary direction — the direction this repository wants.** That is either
luck or design, and there is a third instance available to settle it.

## The third instance, at the object

`headline.py:1638-1640,1684` builds the enrichment null from `by_layer`, which is **every head in the
layer, including the tested ones**:

```python
by_layer.setdefault(k[0], []).append(k)     # the whole band
st += rng2.sample(by_layer[lay], c)          # the null draw
```

The eight sit in layer multiset `{16:1, 17:3, 18:1, 19:2, 22:1}` with `12` heads per layer, so the
expected overlap between a null draw and the tested set is
`3*3/12 + 2*2/12 + 3*1/12 = 1.3333` of `8`. **Every null draw contains, on average, `1.33` of the
heads it is the null for.** `mu`, the band mean the statistic centres on, is also computed over all
`168` including them.

## The direction, predicted BEFORE the run — this is the gauge test

The published numbers say the eight are **less** extreme than matched random:
`T_pub = 0.1154` against a null median of `0.1670`.

**So the eight are small `|centred|` values. Removing them from the pool removes small values, the
null median rises, `T_pub` falls further below it, and `p` must INCREASE** — the claim *"not
enriched"* gets **stronger**.

> **If `p` decreases instead, my account of the leak direction is wrong and the `World F` story below
> dies on the spot.** That is the falsifier, and it is registered here rather than after.

## The two worlds

| | |
|---|---|
| **World A — accident** | three leaks, three directions by chance. Each correction is bookkeeping and nothing general follows. |
| **World F — flattering leak** | **the design leaks in the direction that makes its own nulls easier, structurally.** This repository's claims are *absences*; a reference that contains the tested set is pulled toward it whenever the tested set is unremarkable, and *"not different"* becomes easier. Then every null here is anti-conservative by an unmeasured amount — **and no reviewer checking whether the conclusion was too strong would ever have found it, because each leak makes the conclusion weaker-sounding and safer.** |

`World F` is not a coincidence claim: it is derivable from the design. **A reference drawn from a pool
containing an unremarkable tested set always flatters a null.** What is not derivable is the size.

## Registered thresholds

Population: the `8` heads, band `L14`–`L27`, `qwen2.5-1.5b`, `I_final` and `I_all`,
matched-layer distinct-per-layer, `N = 50000`, the same seeds `headline.py` uses.

| verdict | rule |
|---|---|
| **LEAK-MATERIAL** | `\|delta p\| >= 0.10` in either arm, or a verdict word changes |
| **LEAK-IMMATERIAL** | both below that |
| **DIRECTION-WRONG** | `p` decreases in either arm — the registered falsifier |

Reported regardless: **the expected and realised overlap** between null draws and the tested set, and
the null median with and without the eight in the pool.

## The strongest confound, written before the run

**Removing eight heads from the pool shrinks it, and a smaller pool changes the null's variance as
well as its centre.** A shift in `p` could be the pool size rather than the identity of what was
removed.

**Control, in the same iteration:** `2000` null recomputations that remove **eight random band heads
matched on the layer multiset** `{16:1, 17:3, 18:1, 19:2, 22:1}` instead of the tested eight, giving
the distribution of `delta p` under a size-and-layer-matched removal. **The observed shift is quoted
as a percentile of that.** Inside it, the shift is the price of removing eight heads.

## Positive control

With the eight left in the pool, the recomputation must reproduce the published
`p_distinct_per_layer` of `0.8069038619227615` (`I_final`) and `0.6916861662766745` (`I_all`)
**exactly**, using the same seeds and construction. A recomputation that cannot reproduce the
published null is not the published test.

## What each outcome costs me

**`LEAK-MATERIAL` with `p` rising** confirms `World F`: the repository's central null has been
anti-conservative, its own correction makes it stronger, and **that asymmetry is why none of the
three leaks was ever caught by review.** Every absence claim here would need the qualifier.

**`DIRECTION-WRONG`** kills the pattern and says today's two corrections were luck.

## Boundary

One model, one metric, `8` heads, `50000` draws, `I_final` and `I_all`. This tests the *pool*, not
the statistic: `mu` is left computed over the full band in both arms so the only thing that changes
is what the null may draw. Nothing here re-runs the model.

---

# Amendment 1 — the direction was right, the size is small, and the shift is specific to these eight

Appended 2026-07-29. **No threshold above was changed.**

## Positive controls, both exact

```
I_final   recomputed 0.8069038619227615   published 0.8069038619227615   PASS
I_all     recomputed 0.6916861662766745   published 0.6916861662766745   PASS
```

Bit-for-bit, so this **is** the published test.

**The control earned its keep on the first attempt, which failed.** My first version computed
`p = count / N` and returned `0.8069` against a published `0.8069038619227615`. A `p` quantised to
`1/50000` cannot equal a number that is not a multiple of it — the published one is exactly
`40346/50001`, the add-one bound (`headline.py:797,1288,1575`). **The control caught a convention
error before a single conclusion was read.**

## The registered direction was predicted before the run, and it holds

```
                 null median              p
I_final   0.168493 -> 0.187583    0.806904 -> 0.889842    delta +0.082938
I_all     0.402029 -> 0.413745    0.691686 -> 0.725885    delta +0.034199
```

**`p` increases in both arms, exactly as registered.** Removing the eight from the pool removes small
`|centred|` values, the null median rises, `T_pub` falls further below it. `DIRECTION-WRONG` is off
the table and `World F`'s mechanism is confirmed rather than asserted.

## Registered verdict: `LEAK-IMMATERIAL` — and the confound control says the shift is still *real*

Both deltas are under the registered `0.10`, and no verdict word moves: *"not enriched"* stands in
both arms, more comfortably than published.

**But the shift is not merely the price of removing eight heads.** Against `2000` removals of eight
**random** band heads with the same layer multiset:

```
I_final   null median +0.006880   p95 +0.071319   observed at percentile 0.9805   <- OUTSIDE p95
I_all     null median +0.005380   p95 +0.112158   observed at percentile 0.6470   <- inside
```

**In `I_final` the observed `+0.0829` is beyond the `95`th percentile of a size-and-layer-matched
removal.** So it is specific to *these* eight — as the mechanism predicts, because they are the
unusually *small* ones — and not a pool-size artefact. In `I_all` it is indistinguishable from
removing any eight.

## `World F`, at the size the evidence supports

> **Three leaks today, three corrections, three in the direction that makes this repository's own
> claim stronger — and the third direction was predicted before it was measured.**

That is no longer a coincidence claim. It is derivable: **a reference drawn from a pool containing an
unremarkable tested set is pulled toward that set, and every claim in this repository is an
absence, so every such leak makes the absence easier to declare.** The asymmetry is why none of the
three was caught by review: **each one makes the conclusion sound weaker and safer, and a reviewer
checking whether a claim is too strong will never look there.**

**And the size does not move anything.** `+0.083` and `+0.034` on `p`, `0.4418 -> 0.4870` on the
floor, `7 -> 8` on the count. `World F` is a real property of the design with a small measured
consequence on this artifact — and stating it at that size is the point, because the same design on a
tested set that *was* extreme would leak the other way and by more.

## Boundary

One model, one metric, `8` heads, `50000` draws per arm, `2000` control removals. This tests the
**pool** only: `mu` stays computed over the full band in both arms, so nothing here bounds the
leakage in the centring. The matched-multiset control fixes the layer profile, not the effect-size
profile, so a removal matched on magnitude would give a different percentile. Nothing here re-runs
the model.
