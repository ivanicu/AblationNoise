<!-- unbacked-ok: 2307.15771 2402.15390 2607.01940 -- arXiv identifiers for the self-repair
 literature, not measurements. Same class as the identifiers exempted at the top of README.md: no
 generator here could emit a paper number. -->
# Pre-registration — WHY is the reference distribution wide? Two mechanical candidates, on frozen data

Written 2026-07-28, **before the statistic was computed**, committed alone so git ordering rather than
my word establishes that the thresholds preceded the numbers.

## Why this question and not another audit question

Every step in this repository so far has asked *is this number right*. `122` ledger rows, all of that
shape. **None has asked what the distribution IS** — what makes it wide, why its width changes with
depth, why it is heavy-tailed (excess kurtosis `+7.43`).

That is the question, and it is not answered by more checking.

## The two candidate mechanisms, and they are not the same object

R6 stored, per band head, quantities that no analysis here has ever used together:

| field | what it is |
|---|---|
| `mean_norm` | the size of the head's output — **MAGNITUDE** |
| `displacement_ratio` | how far mean-ablation moves the head's output relative to its own norm — how much of the output is *variable* rather than a constant offset — **INFORMATIVENESS** |
| `cv` | `sd_norm / mean_norm`, a second magnitude-normalised variability measure |

| | |
|---|---|
| **World M — MAGNITUDE** | the floor is wide because heads differ in how *big* their writes are. A big head moves the logits more, whatever it encodes. Then the reference distribution is a distribution of norms wearing a causal costume, and "is this head unusual" mostly asks "is this head large". |
| **World I — INFORMATIVENESS** | the floor is wide because heads differ in how much *variable* content they carry. A head whose output is nearly constant across items contributes a bias the readout has already absorbed; a head whose output swings carries item-specific information whose removal actually changes the answer. |

These imply different things about every result in this repository. Under **M**, the eight published
heads sitting inside the floor is close to a statement about their size. Under **I**, it is a
statement about their content.

## The strongest confound, written before the run, with its control in the same iteration

**`mean_norm` and `displacement_ratio` are not independent, and a raw correlation is expected under
BOTH worlds** — a head that writes more has more room to both move the residual stream and shift the
logits. A bare Spearman would therefore confirm whichever world I looked at first.

**The control is a partial correlation:** each predictor's Spearman with `|centred effect|`
*controlling for the other*, computed on ranks. Only the partials are used for the verdict; the raw
correlations are reported beside them so the shrinkage is visible.

**Second confound: depth.** Both norms and effects grow with layer. A pooled correlation over
`L14`–`L27` can be produced entirely by both quantities rising with depth, and this repository has
already been caught once by exactly that (one edge went `-0.1885` pooled to `+0.0060` within-layer, a
sign flip). **Every statistic below is therefore computed BOTH pooled and within-layer**, and the
within-layer version is the one the verdict uses.

## Registered thresholds

Population: the `168` band heads `L14`–`L27` of `qwen2.5-1.5b`. Effect = `|drop - mu_band|` from
`R10_exhaustive`, the centred statistic this repository actually uses.

| verdict | rule (on the WITHIN-LAYER partials) |
|---|---|
| **MAGNITUDE-DOMINATED** | `partial(|eff|, norm \| disp) >= 0.30` **and** `partial(|eff|, disp \| norm) < 0.15` |
| **INFORMATION-DOMINATED** | the reverse |
| **BOTH** | both `>= 0.30` |
| **NEITHER** | both `< 0.15` |

**`NEITHER` is the outcome I should want and expect to dislike**: it would mean the two cheapest
mechanical explanations of the floor's width are both wrong, and the width is caused by something
this repository has not measured — which is a bigger finding than either world winning.

`alpha = 0.05`, `N_PERM = 20000`, `N_BOOT = 10000`, seed `20260728`. Permutation null: shuffle
`|eff|` within layer, so the null preserves the depth structure the confound above is about.

## Positive controls

1. **The predictors must vary.** `mean_norm` and `displacement_ratio` are reported with their range
   and IQR across the `168` heads. A predictor with no spread cannot explain any spread, and a null
   from one would be silence rather than an acquittal.
2. **The instrument must detect a planted relationship.** A synthetic effect vector built as
   `mean_norm` plus noise must return a large positive partial for `norm` and a small one for `disp`.
   A partial-correlation routine that cannot recover a relationship it was handed is not an
   instrument.
3. **Sanity on the known edge.** `cv` and `displacement_ratio` should themselves correlate, since
   both measure output variability. If they do not, one of them does not mean what its name says.

## Boundary

One model, one metric, one task, `I_final` only, `168` band heads, and **`R6`'s diagnostic was
computed on its own item set** — if that differs from `R10`'s, the two vectors are not paired on
identical data and the correlation is attenuated by that mismatch. **This is checked in the code and
reported, not assumed.** Nothing here is about `I_all`, and nothing here establishes causation between
the predictors and the effect: three quantities measured on the same heads can share a cause.

---

# Amendment 1 — the outcome, and why the verdict WORD is misleading on its own

Appended 2026-07-28 after running `mechanism()`. Thresholds above unchanged.

## Positive controls, all three

| control | returned |
|---|---|
| predictors have spread | `mean_norm` `0.6735` → `20.1064` (`30×`); `displacement_ratio` `0.0314` → `0.7535` (`24×`) |
| a planted relationship is recovered | effect built as `mean_norm` + noise returns partial `0.9288` for norm, `0.0764` for disp |
| `cv` should track `displacement_ratio` | **Spearman `0.9998`** — see below, this is a finding, not a pass |

## The registered verdict: `MAGNITUDE-DOMINATED`

```
within-layer partial (|centred effect|, mean_norm | displacement)   +0.3388   p = 0.00015
within-layer partial (|centred effect|, displacement | mean_norm)   +0.0869   p = 0.3028
                              depth-preserving null, 97.5th          0.1625 / 0.1643
```

Magnitude clears `0.30`; informativeness sits below `0.15` and inside its own null. By the rule as
written, that is `MAGNITUDE-DOMINATED`.

## **Read the size, not the label — and the size says the opposite**

A rank partial of `0.3388` is `0.1148` of the rank variance.

```
rank variance attributable to magnitude          0.1148
rank variance attributable to informativeness    0.0075
UNEXPLAINED                                      0.8777
```

**`88%` of the ordering is explained by neither.** So the honest statement is not *"the floor is a
distribution of head sizes"*. It is:

> **Of the two cheapest mechanical explanations of the reference distribution's width, one accounts
> for about a ninth of it and the other for nothing. The width is mostly caused by something this
> repository has not measured.**

That is materially the `NEITHER` branch's meaning arriving through the `MAGNITUDE-DOMINATED` branch's
door, and it is recorded that way rather than quoted by its verdict word. The emitter now returns
`rank_variance_unexplained` beside the verdict so the two cannot be separated.

## The depth control ran in the direction I did not expect

```
pooled partial (effect, norm | disp)        +0.1299
within-layer                                +0.3388     2.61x LARGER
```

Pooling across `L14`–`L27` **masks** the magnitude relationship rather than manufacturing it. The
reason is visible in the data: `mean_norm` and effect both rise with depth, but not in step, so the
between-layer spread adds variance to both axes without adding covariance. **Every previous use of a
pooled correlation in this repository was defended on the grounds that pooling inflates. Here it
deflates**, so "pooled is the conservative choice" is not a general fact and was being used as one.

## `cv` and `displacement_ratio` are one measurement with two names

Spearman `0.9998` between them. `displacement_ratio` was introduced as a manifold-geometry quantity
and `cv` as a normalised variability; **on these 168 heads they order the heads identically.** So the
`INFORMATIVENESS` arm of this test was, operationally, normalised output variability — a legitimate
proxy, but not the geometric quantity its name implies, and `D103`'s critique of
`displacement_ratio` therefore applies to `cv` too. Two names for one number is how a repository
convinces itself it has two independent measurements.

## What is now open, and it is the real question

The residual `0.8777` is the object. Neither how much a head writes nor how variable its output is
predicts how much removing it moves the answer. **Candidates this repository has never touched, in
the order they are cheapest to test:**

1. **Self-repair / the Hydra effect** — `2307.15771`, `2402.15390`, and `2607.01940` (published `25`
   days before this project began), which states the mechanism directly: *"first-order scoring is
   natural when component importance is additive, but becomes misleading when a transformer
   self-repairs."* **This literature is cited nowhere in this repository** and it supplies exactly
   the missing term: the measured effect is the true contribution *minus what the network restores*.
   It also predicts the sign result — `L16H3` and `L22H7` improve the margin when removed, which is
   over-compensation, not absence of a role.
2. **Alignment of the head's write with the readout direction** — a large write orthogonal to the
   room-token logit difference moves nothing. Computable from weights, no GPU.
3. **Position of the head's write relative to where the query is read** — `R19`, running now.

## Boundary

One model, one metric, one task, `I_final`, `168` band heads, `n = 12` per layer so each within-layer
statistic is noisy and only their mean is read. Correlation, not causation: three quantities measured
on the same heads can share a cause.
