# Amendment 3 — the question is `w`, and a verdict word cannot hold a `w`

Registered 2026-07-29, after the power run, before the sweep. Commit this file alone.

## Why the last result is not enough

`STEP-LIKE` in `9` of `10`, `0` underpowered, both matchings agreeing. Three things are wrong with
reading that as an answer.

1. **The ramp planted was a straight line across all `28` layers.** Amendment 1 defined World C as
   *"a broad elevation across the last several layers, with no jump anywhere."* A global line is not
   that. The verdict excludes a world nobody proposed and is silent on the live one.
2. **Every observed value sits at the floor of the step interval.** `x` lands `0.1` to `0.6` above
   the lower edge while the interval runs to about `8`. Inside the central `80%` is true and
   misleading — that is where the step world is *least* likely.
3. **Amendment 1 already said this.** *"The right question is HOW LOCALISED, a continuous quantity,
   not WHERE, a discrete one."* The next thing I did was run a two-point test.

## The object

A one-parameter family: **transition width `w`**. Concentration is flat, rises linearly over `w`
layers centred on the fitted split, then flat again. `w = 1` is the step, `w = n` is the ramp. The
two plants already run are the two endpoints of this family and nothing between them was ever drawn.

**The deliverable is an interval on `w`, per model × support × statistic. Not a word.**

`w` is a number with a unit — layers — that can be compared across cells, across supports, across
models, and against any future checkpoint. A verdict word cannot be compared with anything.

## Method

Grid `w` in `{1, 2, 3, 4, 6, 8, 14, 28}`. At each `w`, `400` replicates at the **observed** amplitude
and residual scatter for that cell, sharpness on the `min_side=4` curve, split refitted per replicate.

**Admissible set** = every `w` whose central `80%` sharpness interval contains the observed `x`.
Report the set. If it spans the whole grid, the sweep is uninformative and that is the result.

## Controls, both required before the real data is read

1. **Recovery.** Plant a known `w = 3` at the observed amplitude and noise, then run the inversion on
   it. The admissible set **must contain `3`**, in `>= 8` of the `10` cell configurations. An
   inversion that cannot recover a planted width says nothing about an unknown one.
2. **Endpoint recovery.** Same at `w = 1` and `w = 28`. Each must be admissible for its own plant.
   If `w = 1` data admits `w = 28`, the sweep has no resolution anywhere and no interval is read.

## The confound, written before the run

**`w` and effect size are entangled**: spreading a fixed jump over more layers lowers the fitted `t`,
so a wide-`w` plant is also a weaker plant, and sharpness could be tracking strength rather than
localisation. Two arms:

- **A — amplitude fixed** at the observed jump for every `w`.
- **B — amplitude retuned** per `w` so the median fitted `t` matches the observed `t`.

If the two arms give different admissible sets, **the result is UNVERIFIED and the disagreement is
the finding** — it would mean sharpness cannot separate width from strength at this `n`.

## Registered reading

- **LOCALISED** — arms agree and the admissible set excludes `w >= 8` in `>= 8` of `10` cells.
- **BROAD** — arms agree and the set excludes `w <= 2` in `>= 8` of `10`.
- **UNINFORMATIVE** — the set spans the grid in `>= 5` of `10`. Checked first, wins outright.
- **UNVERIFIED** — the arms disagree, or a control fails, or anything else.
