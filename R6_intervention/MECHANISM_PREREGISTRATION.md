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
