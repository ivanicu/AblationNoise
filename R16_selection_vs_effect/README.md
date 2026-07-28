<!-- unbacked-ok: 2504.13752 -- an arXiv identifier, not a measurement: the paper that states
 attention's unreliability as a proxy is established background. No generator here emits it. -->

# R16 — the audited heads were **selected by attention** and **measured by ablation**

Fifteen rounds treated *"the eight published single-head effects"* as a given set. **Reading the
source experiment — rather than the note I wrote about it — says where the set came from.**

```
E132   scored room_att and name_att over ALL 28×12 heads, took the top by an attention ratio
E132b  causally tested SEVEN of those  (its `sel` dict has 7 keys)
       plus L22H7, which E132 ranked FIRST on room attention  (pc_L22H7_room_rank: 0)
```

**So the audited set is "the heads attention picked", and the audit measures them with ablation.**
That is a two-instrument comparison, and it had never been run.

## The two instruments anti-correlate

Over the `168` band heads — same model, same items, same vocabulary, `E132`'s own attention arrays
frozen into [`results/`](results/e132_attention_scores.json):

```
Spearman(|centred ablation|, room attention) = −0.1885
Spearman(|centred ablation|, name attention) = −0.3952
```

**Both negative.** They do not merely fail to agree.

```
head        ablation   room rank   name rank            top-5 by room-att
L18H0         1.1882         142         125            → ablation ranks 41 · 56 · 61 · 52 · 3
L27H2         1.0504           6         157
L25H4         0.9486           5          94            top-5 by name-att
L21H11        0.9024          50         133            → ablation ranks 129 · 137 · 157 · 88 · 167
L19H11        0.8052         162         102
L19H6         0.7470         141         155
L26H6         0.6204          17         118
L19H9         0.5975         119          84
L15H7         0.5269         168         168   ← last of 168 on BOTH, and 9th by ablation
L16H3         0.5147         120         126
```

**`L15H7` attends less than any other head in the band, on both criteria, and ablating it is the
9th largest effect.**

### It is a **magnitude** effect, not a direction one — and the negative number invites the wrong reading

`|drop|` throws away the sign, and this project has already shown the sign matters: `100` positive **[⚠ that split is RAW; centred on the band mean `+0.0479` — the statistic every verdict in this repository actually uses — it is `64` above and `104` below, and the qualitative reading inverts. `D90`.]**
against `68` negative in this band, and `7` of the `9` clearing heads clear by **helping**. A reader
given only `−0.40` will fill in *"so high-attention heads help when ablated."* **They do not.**

```
                      on |drop|     on SIGNED drop
room attention          −0.1885         −0.0583
name attention          −0.3952         −0.1142        ~3× weaker
```

**Attention picks heads that do *less*, in either direction.** But the top quartile does carry a
direction:

```
name-att quartile   n    mean signed drop   pos/neg
Q1 (lowest)        42          +0.0504       21/21
Q2                 42          +0.0201       18/24
Q3                 42          −0.0394       16/26
Q4 (highest)       42          −0.0311        9/33
```

**`Q4` is `9` positive against `33` negative** — the heads that attend most to names do tend to
*hurt* when ablated, which is the direction you would expect if they do something. **Their effects
are simply small, which is exactly why they rank low on `|ablation|`.**

## This is **not** a discovery, and saying so is the point

That attention weight is an unreliable proxy for causal importance is **established background**.
[`arXiv 2504.13752`](https://arxiv.org/abs/2504.13752) (Cohen-Wang, Chuang, Madry) states it in its
abstract: *"Naive approaches to attribute model behavior with attention … have been found to be
unreliable."*

> **Positive control on that query, because this repository's opening claim died to exactly this
> mistake:** the search returned one squarely relevant paper, so it was **not silent** — and it also
> returned cloud removal and Boltzmann attention, so it is **noisy and no completeness is claimed.**

**What R16 adds is not the direction but the consequence for this audit.** The eight heads under
audit were selected by **exactly the proxy that is known to fail**, which turns

> *"the heads ablation flags loudest were never identified"*

from a curiosity into a result **with a named cause**: they were never identified because the
identifying instrument anti-correlates with the measuring one, at `−0.19` and `−0.40` on this task.

## What R16 does not claim

* **It does not say attention is wrong and ablation is right.** Two instruments disagreeing says
  neither is a proxy for the other; it does not rank them. [R14](../R14_position_vs_binding/) showed
  the model does not use the task's positional degeneracy, and nothing here identifies a mechanism.
* **One model, one task, one vocabulary, `k=1`, band `L14–27`.** `E132`'s `room_att` and `name_att`
  are its own specific definitions at the final position; another attention statistic could differ.
* **`−0.19` and `−0.40` are modest.** They are not "attention predicts the opposite"; they are
  "attention predicts slightly worse than nothing" on this pairing.
* **The correction to my own note:** it said *"five read-head candidates, one proven copy head, two
  unlabelled."* The source says **seven selected candidates plus one externally-known copy head.**
  The composition was wrong in a file I wrote about an experiment I did not re-open until now.
