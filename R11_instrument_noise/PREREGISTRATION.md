# R11 — measure the instrument's noise instead of inferring it

Written and committed **before** either run is launched. 2026-07-28.

## Why this round exists

[R10](../R10_exhaustive/) established the floor by measuring every head once. One step later the
front page tried to get the *other* noise — the instrument's own — for free, by reading it off the
quietest layer. **That was withdrawn:** a layer's spread tracks its effect scale at Spearman
`+0.962`, so a quiet layer is quiet in *both* terms and bounds only the item noise of equally quiet
heads. The eight published effects are not quiet heads.

So the distinction the front page needs —

| | |
|---|---|
| **not measurable** | below what the instrument resolves on `120` items |
| **not distinctive** | resolvable, and a random head of the same size does the same |

— has one settled half (`distinctive`: `0` of `8`) and one `UNVERIFIED` half. This round measures
the missing denominator directly.

## The two runs

Both use `R10_exhaustive/run.py`, which now stores `per_head_sem = sd_over_items / sqrt(n)` — a
quantity every previous run computed and discarded.

| run | items | what it gives |
|---|---|---|
| **A** | the published set (`seeds 3000..3400`) | the SEM *of the numbers already published* |
| **B** | `--seed-offset 400` → `seeds 3400..3800`, **disjoint by construction** | an independent replicate of every head |

## What each outcome means — fixed now, not after

### 1 · Measurability, per head — replaces the withdrawn threshold

`|drop| / (2 · SEM)` on run A. `> 1` ⇒ resolvable at 2σ by this instrument on this item set.

* **The three large effects clear** → `measurable` becomes CONFIRMED, the front page's
  measurable-but-not-distinctive framing stands, and the withdrawn bound turns out to have had the
  right answer for the wrong reason. *That is not vindication; it is a coincidence, and will be
  labelled one.*
* **They do not clear** → the framing is wrong in the opposite direction: the effects were never
  resolvable, and "not distinctive" was never the interesting half.

### 2 · Is the SEM the whole story? — run A vs run B

For each band head, `|drop_A − drop_B|` against `2 · sqrt(SEM_A² + SEM_B²)`.

* **Disagreements sit inside that band** ⇒ item sampling explains run-to-run variation; the SEM is
  the instrument's noise and can be used as a denominator.
* **Disagreements are systematically larger** ⇒ **the SEM UNDERSTATES the noise.** Something else
  varies run to run, and every per-head number in this repository — including R10's exhaustive
  floor — carries an unmodelled term. This is the outcome that costs the most and it is the reason
  run B exists.

### 3 · KILL — is the floor itself item-set-dependent?

Exhaustive band floor on run A vs run B.

> **Pre-registered threshold: if the two exhaustive floors differ by more than `20%`, the floor is a
> property of the item set as well as of the model**, and every "inside the floor" claim in this
> repository needs an item-set scope it does not currently carry — including the headline.

`20%` is chosen because the 30-draw *sampling* interval already spans `2.7×`; a floor that moves
more than a fifth between two exhaustive measurements is moving for a reason sampling does not
explain. **I do not know which way this goes.**

## What this round cannot do

* **One model, one task, one vocabulary, `k=1`.** Nothing here transfers to `k>1`, to other
  readouts, or to the other three families.
* **Two item sets is `n=2`.** A difference below the threshold is not evidence that the floor is
  item-set-*independent* — it is one comparison, and [R4's lesson](../R4_predictability/) is that
  two points do not establish a law.
* **The SEM is the noise of the mean, not of the mechanism.** A head whose effect is real but
  item-dependent will show a large SEM and be called unresolvable. That is a correct statement about
  *this readout at n=120*, not about the head.
