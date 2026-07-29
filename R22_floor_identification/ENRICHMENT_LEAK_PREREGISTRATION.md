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
