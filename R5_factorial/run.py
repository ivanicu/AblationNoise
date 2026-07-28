#!/usr/bin/env python3
"""R5 — WHICH FACTOR MADE R1 AND R2 DISAGREE? A 2x2 on one model and one task.

Pre-registration: R5_PREREGISTRATION.md, committed at 05a44ce before this file existed.

    factor A  site     final position only  |  all positions
    factor B  readout  4-way room margin    |  full-vocab KL vs the unablated distribution

EACH CELL MEASURES ITS OWN NULL. A larger intervention raises the effect and the floor together, so
a cell that borrowed another cell's null would confound the very thing this design separates.

EACH CELL ALSO CARRIES ITS OWN POSITIVE CONTROL (all heads of one layer), because R2 established
that a cell resolving nothing must be distinguishable from a cell whose instrument is dead.
"""
from __future__ import annotations

import argparse
import sys
import json
import random
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from task import PERSONS, OBJECTS, ROOMS

torch.set_num_threads(20)
N_ITEMS = 90
N_DRAWS = 30
DRAW_SEED = 20260727
SEEDS = list(range(3000, 3400))
ROOMS4 = ['stone', 'iron', 'glass', 'water']
MECH = [(22, 7)]                       # L22H7, the copy head established by E123
PC_LAYER = 22                          # positive control: every head of this layer


def bindings(seed, rooms):
    r = random.Random(seed)
    ps, obs = list(PERSONS), list(OBJECTS)
    assigned = (list(rooms) * 4)[:len(ps)]
    r.shuffle(ps); r.shuffle(obs); r.shuffle(assigned)
    return {ps[i]: (obs[i], assigned[i]) for i in range(len(ps))}


def prompt(q, b):
    lines = [f"{p} owns the {b[p][0]}. The {b[p][0]} is in the {b[p][1]} room." for p in PERSONS]
    return '\n'.join(lines + [f"Question: Which room should {q} go to find their object?",
                              "Answer: The"])


@torch.no_grad()
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--out', default='results/r5_factorial')
    ap.add_argument('--dtype', default='float32', choices=['float32', 'bfloat16'])
    ap.add_argument('--max-gpu', default='', help='e.g. 13GiB — spill remaining layers to CPU')
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    load_kw = dict(trust_remote_code=True, torch_dtype=getattr(torch, args.dtype),
                   attn_implementation='eager')
    if args.max_gpu and torch.cuda.is_available():
        # An 8B in bf16 is 15 GB against a 15.5 GB card and OOMs by ~20 MiB with activations.
        # Spilling the tail layers to CPU keeps the forward hooks intact -- they are registered on
        # modules, not devices -- and that was verified before trusting any number from such a run:
        # ablating every head of an OFFLOADED layer moves the logits, so the hooks bite there.
        load_kw.update(device_map='auto', max_memory={0: args.max_gpu, 'cpu': '40GiB'})
    else:
        load_kw.update(device_map='cuda' if torch.cuda.is_available() else 'cpu')
    m = AutoModelForCausalLM.from_pretrained(args.model, **load_kw).eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH

    import sys
    from detectors.readout_tokens import check_readout
    rep = check_readout(tok, ROOMS4)
    print(f"  readout detector: {rep.verdict}")
    if not rep.ok():
        raise SystemExit(f"REFUSED: {rep.why}")
    rid = rep.scored_ids
    pl = rep.shared_prefix_len
    single = [p for p in PERSONS if len(tok.encode(' ' + p, add_special_tokens=False)) == 1 + pl]

    # THE MECHANISM IS IDENTIFIED IN-RUN, BY THE SAME OPERATIONAL RULE ON EVERY MODEL: the head with
    # the greatest final-position attention to the correct room token, on items the model gets right.
    # L22H7 was hard-coded for qwen2.5-1.5b because E123 established it there; hard-coding it for a
    # second model would import a head index across checkpoints, which is the mistake R2 avoided by
    # deriving induction heads per model. The identification uses ATTENTION and the outcome uses
    # margin/KL, so selection and outcome do not share a definition.
    def identify_copy_head(probe):
        acc = np.zeros((NL, NH))
        for enc, cor, _ in probe:
            out = m(**enc, output_attentions=True, use_cache=False)
            ids = enc['input_ids'][0]
            tgt = (ids == rid[cor]).nonzero().flatten()
            if len(tgt) == 0:
                continue
            for L in range(NL):
                a = out.attentions[L][0][:, -1, :]          # (H, S) final-position attention
                acc[L] += a[:, tgt].sum(dim=1).float().cpu().numpy()
        L, h = np.unravel_index(int(acc.argmax()), acc.shape)
        return [(int(L), int(h))], float(acc.max() / max(1, len(probe)))

    active: dict[int, set[int]] = {}
    site = {'mode': 'final'}

    def mk(L):
        def pre(mod, a):
            if L not in active:
                return a
            x = a[0].clone()
            for h in active[L]:
                if site['mode'] == 'final':
                    x[0, -1, h * HD:(h + 1) * HD] = 0
                else:
                    x[..., h * HD:(h + 1) * HD] = 0
            return (x,) + a[1:]
        return pre

    for L in range(NL):
        m.model.layers[L].self_attn.o_proj.register_forward_pre_hook(mk(L))

    # ── build the item set once; both readouts use the same items ────────────────────────────
    items = []
    for s in SEEDS:
        b = bindings(s, ROOMS4)
        q = next((p for p in single if p in b), None)
        if q is None:
            continue
        enc = {k: v.to(m.device) for k, v in tok(prompt(q, b), return_tensors='pt').items()}
        active.clear()
        lg = m(**enc, use_cache=False).logits[0, -1]
        if max(ROOMS4, key=lambda r: lg[rid[r]].item()) != b[q][1]:
            continue
        items.append((enc, b[q][1], lg.float().log_softmax(-1).clone()))
        if len(items) >= N_ITEMS:
            break
    print(f"  n items {len(items)}")

    def measure(heads, mode, readout):
        site['mode'] = mode
        active.clear()
        for (L, h) in heads:
            active.setdefault(L, set()).add(h)
        vals = []
        for enc, cor, base_lp in items:
            lg = m(**enc, use_cache=False).logits[0, -1]
            if readout == 'margin':
                v = lg[rid[cor]].item() - max(lg[rid[r]].item() for r in ROOMS4 if r != cor)
            else:                                    # full-vocab KL(base || ablated)
                lp = lg.float().log_softmax(-1)
                v = float((base_lp.exp() * (base_lp - lp)).sum())
            vals.append(v)
        active.clear()
        return float(np.mean(vals))

    mech, mech_attn = identify_copy_head(items[:30])
    print(f"  copy head identified in-run: L{mech[0][0]}H{mech[0][1]}  "
          f"(mean final-position attention to the correct room token {mech_attn:.3f})")
    globals()['MECH'] = mech

    rng = random.Random(DRAW_SEED)
    pool = [(L, h) for L in range(NL // 2, NL) for h in range(NH) if (L, h) not in mech]
    draws = [rng.sample(pool, len(MECH)) for _ in range(N_DRAWS)]
    pc = [(mech[0][0], h) for h in range(NH)]   # every head of the mechanism's own layer

    cells = {}
    for mode in ('final', 'all'):
        for readout in ('margin', 'kl'):
            base = measure([], mode, readout)
            eff = measure(mech, mode, readout) - base
            nulls = np.array([measure(d, mode, readout) - base for d in draws])
            pcv = measure(pc, mode, readout) - base
            sd = float(nulls.std(ddof=1))
            key = f"{mode}_{readout}"
            cells[key] = {
                'site': mode, 'readout': readout, 'baseline': base,
                'effect': eff, 'positive_control': pcv,
                'null_mean': float(nulls.mean()), 'null_sd': sd,
                'null_median': float(np.median(nulls)),
                'null_p10': float(np.percentile(nulls, 10)),
                'null_p90': float(np.percentile(nulls, 90)),
                'effect_pct_in_null': float((nulls < eff).mean() * 100),
                'pc_pct_in_null': float((nulls < pcv).mean() * 100),
                'clears_p10p90': bool(eff < np.percentile(nulls, 10) or eff > np.percentile(nulls, 90)),
                'pc_clears': bool(pcv < np.percentile(nulls, 10) or pcv > np.percentile(nulls, 90)),
                'ratio_effect_over_2sd': float(abs(eff) / (2 * sd)) if sd else float('nan'),
            }
            c = cells[key]
            print(f"  {key:<14} base {base:8.4f}  effect {eff:+9.4f}  null med {c['null_median']:+8.4f}"
                  f"  [p10 {c['null_p10']:+7.4f}, p90 {c['null_p90']:+7.4f}]  "
                  f"eff@{c['effect_pct_in_null']:5.1f}pct  "
                  f"{'CLEARS' if c['clears_p10p90'] else 'inside'}  "
                  f"| PC {pcv:+9.4f} {'ok' if c['pc_clears'] else 'DEAD'}")

    res = {'model': args.tag, 'n_items': len(items), 'n_draws': N_DRAWS,
           'mechanism': [list(x) for x in mech], 'mechanism_attn': mech_attn,
           'dtype': args.dtype, 'mechanism_identified': 'in-run: max final-position attention to the correct room token', 'rooms': ROOMS4, 'cells': cells}
    Path('results').mkdir(exist_ok=True)
    out = f"{args.out}_{args.tag}.json"
    json.dump(res, open(out, 'w'), indent=2, default=float)
    print(f"  -> {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
