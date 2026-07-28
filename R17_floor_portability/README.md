# R17 — the headline is **not** an artifact of measuring where the floor is largest

[R15](../R15_shuffled_scan/) found that the noise floor tracks the task's baseline margin at
Spearman `+0.8810`. That turns the repository's own headline into a suspect.

> The eight published heads were measured on the configuration with the **highest** margin available
> — every answer at line `0`, the primacy position, margin `4.477`. **The floor sits in the
> denominator of `×floor`, so a larger floor makes every head look smaller.** The finding was
> produced at exactly the configuration most favourable to it.

That is a directional bias pointing at my own conclusion, and R15's scan makes it free to check.

| world | if the eight's `×floor` rises materially on the shuffled task | if it does not |
|---|---|---|
| **A** — `7 of 8 inside the floor` is a fact about those heads | dies | survives |
| **B** — it is an artifact of the highest-floor configuration | survives | dies |

## World B is killed

```
head       UNSHUF |c|  xfloor  rank      SHUF |c|  xfloor  rank   numerator ratio
L16H3          0.5147    1.06    10        0.3705    0.92    14        0.72
L17H0          0.0856    0.18    77        0.0993    0.25    62        1.16
L17H7          0.0831    0.17    79        0.0885    0.22    64        1.06
L17H11         0.0100    0.02   158        0.0366    0.09   112        3.67
L18H9          0.0069    0.01   162        0.0294    0.07   119        4.28
L19H0          0.0325    0.07   129        0.0290    0.07   121        0.89
L19H5          0.0106    0.02   157        0.0276    0.07   123        2.59
L22H7          0.1797    0.37    41        0.0778    0.19    69        0.43

floor       0.4870  ->  0.4023   (0.826x)
clearing      1 of 8  ->    0 of 8
```

**The `17%` lower floor rescued nothing.** `L16H3`, the only head that cleared, falls from `1.06×`
to `0.92×` — because its **numerator** fell `0.72×` while the denominator fell only `0.826×`.

## Two narrative-friendly patterns in that same table, and both die

Both point toward the conclusion this repository already argues. **That is why the controls were
run, not a reason to skip them.**

### (1) Seven of eight rise in rank — regression to the mean

```
the eight, mean rank            101.6  ->  85.5      shift  -16.1
global regression slope of (shuffled rank - 84.5) on (unshuffled rank - 84.5)   0.6092
predicted mean rank                        94.9      shift   -6.7
residual                                   -9.43
null over 20,000 random 8-head sets: sd 13.29        one-sided p = 0.2351
```

**Ranks regress toward the middle for every head, not just these eight.** The residual is inside the
null. **No finding.**

### (2) `L22H7`'s raw effect more than halves — and it is inside the band's own IQR

`L22H7` falls to `0.433×` while the floor fell only to `0.826×`, and it is the **only** one of the
eight to drop in rank. A copy head whose source line stops being fixed is a story that writes itself.

```
median band head's numerator ratio    0.723        IQR  0.424 - 1.392
L22H7                                 0.433        26.2nd percentile
```

**Inside the IQR, low-normal, not anomalous.** It is also the noisiest of the eight —
[R11](../R11_disjoint_items/) measured it at `1.27×` its own SEM, the weakest margin of the set.
**No finding.**

## This is the first round that attacked a headline claim and did not move it

**No row is added to [`defects.json`](../defects.json).** Nothing in the artifact was wrong. The two
patterns above were caught before they were written down, and a pattern caught before shipping is
not a defect in the artifact — counting it would inflate the ledger with the author's own drafts.

## What R17 does not claim

* **`0 of 8` is not stronger evidence than `1 of 8`.** It is the *same* evidence at a different
  floor, and the count moving down by one is well within what a `17%` floor change can do to a head
  sitting at `1.06×`.
* **One alternative configuration**, one shuffle seed (`90210`). World B is killed *for this
  contrast*; a configuration with an even lower floor was not tested and could in principle differ.
* **Neither control proves the absence of an effect.** `p = 0.2351` on `n=8` heads is a wide test —
  it says the observed shift is unremarkable, not that no shift exists.
