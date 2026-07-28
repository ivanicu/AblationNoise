#!/usr/bin/env python3
"""R6 DIAGNOSTIC — is mean-ablation a GENTLER intervention, or nearly the IDENTITY?

WHY THIS EXISTS. R6's mean and resample arms produced small effects, small floors, and on two of
four models a positive control that does not clear its own single-head null. Two explanations
survive that observation and they are not the same claim:

    G  GENTLER      writing a plausible on-distribution value really does perturb the model less,
                    and it perturbs the MECHANISM more than it perturbs random heads -- so the
                    signal-to-floor ratio genuinely falls.
    I  IDENTITY     a head's output at the FINAL POSITION carries little item-specific variance,
                    so its mean over items IS approximately its value on any given item. Then
                    mean-ablation is not a gentle intervention; it is nearly no intervention, and
                    every small number in R6 is arithmetic rather than a fact about ablation.

THE SEPARATOR IS CHEAP AND NEEDS NO ABLATION AT ALL. Capture each head's final-position output
slice over the item set -- one clean forward per item, the same pass R6's runner already does --
and report, per head,

    cv = || sd over items of the slice ||  /  || mean over items of the slice ||

    I predicts  cv -> 0        (mean == the value, so replacing one with the other does nothing)
    G predicts  cv is O(1)     (the mean is a real distance away from any given item's value)

A quantitative form of the same prediction, which is the one that decides it: the mean-ablation
displacement is exactly `slice_i - mean_slice`, whose typical norm is the sd term above. Compare it
to the zero-ablation displacement, which is `slice_i` itself, i.e. the mean term plus the sd term:

    displacement_ratio = || slice_i - mean ||  /  || slice_i ||

    I predicts  displacement_ratio << 1   -- mean-ablation moves the residual stream far less
    G predicts  displacement_ratio ~ 1    -- both interventions move it comparably, and the
                                            difference in outcome is about WHERE they move it to

STOPPING RULE, written before running: median displacement_ratio over band heads < 0.2 on a
majority of models -> world I, and R6's arms are reported as near-identity rather than as gentle.
Above 0.5 -> world G survives and R6's failed positive controls are a real dynamic-range result.
In between -> neither, and say so.

    python3 R6_intervention/diag_item_variance.py --model <path> --tag <name>
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from task import PERSONS, OBJECTS  # noqa: E402

# THE RESULT FILE MUST KNOW WHICH CODE PRODUCED IT. A sibling project recorded this exact defect:
# a fix was announced while the running workers kept executing the pre-edit file, and nothing in
# the output could have shown it. Its durable fix -- stamp sha256(source) into every row -- was
# never carried here, and on 2026-07-28 an audit found 40 result files with zero provenance and
# 12 of them produced by code that has since been edited.
_CODE_VERSION = __import__("hashlib").sha256(
    __import__("pathlib").Path(__file__).read_bytes()).hexdigest()[:8]

torch.set_num_threads(20)
N_ITEMS = 120
SEEDS = list(range(3000, 3400))


def bindings(seed, rooms):
    r = random.Random(seed)
    ps, obs = list(PERSONS), list(OBJECTS)
    assigned = (list(rooms) * 4)[:len(ps)]
    r.shuffle(ps); r.shuffle(obs); r.shuffle(assigned)
    return {ps[i]: (obs[i], assigned[i]) for i in range(len(ps))}


def prompt(query, b):
    lines = [f"{p} owns the {b[p][0]}. The {b[p][0]} is in the {b[p][1]} room." for p in PERSONS]
    return '\n'.join(lines + [f"Question: Which room should {query} go to find their object?",
                              "Answer: The"])


def resolve_o_proj(layer):
    for an in ('self_attn', 'attention', 'attn', 'self_attention'):
        att = getattr(layer, an, None)
        if att is None:
            continue
        for pn in ('o_proj', 'wo', 'out_proj', 'dense', 'proj'):
            proj = getattr(att, pn, None)
            if proj is not None:
                return f'{an}.{pn}', proj
    return None, None


@torch.no_grad()
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--rooms', nargs='*', default=['stone', 'iron', 'glass', 'water'])
    ap.add_argument('--out', default=str(HERE / 'results' / 'r6_diag_item_variance'))
    args = ap.parse_args()
    rooms = args.rooms

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        args.model, trust_remote_code=True, torch_dtype=torch.float32,
        device_map='cuda' if torch.cuda.is_available() else 'cpu',
        attn_implementation='eager').eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    lo, hi = NL // 2, NL - 1

    from detectors.readout_tokens import check_readout
    rep = check_readout(tok, rooms)
    if not rep.ok():
        raise SystemExit(f"REFUSED: {args.tag} readout is {rep.verdict}. {rep.why}")
    rid, pl = rep.scored_ids, rep.shared_prefix_len
    single = [p for p in PERSONS if len(tok.encode(' ' + p, add_special_tokens=False)) == 1 + pl]

    cap: dict[int, list[torch.Tensor]] = {L: [] for L in range(NL)}
    grab = {'on': False}

    def mk(L):
        def pre(mod, a):
            if grab['on']:
                cap[L].append(a[0][0, -1].detach().float().cpu().clone())
            return a
        return pre

    for L in range(NL):
        _, proj = resolve_o_proj(m.model.layers[L])
        proj.register_forward_pre_hook(mk(L))

    # Same item filter as the runner, so the diagnostic describes the population R6 measured
    # rather than a different one that happens to be easier to collect.
    items, n = [], 0
    for s in SEEDS:
        b = bindings(s, rooms)
        q = next((p for p in single if p in b), None)
        if q is None:
            continue
        enc = {k: v.to(m.device) for k, v in tok(prompt(q, b), return_tensors='pt').items()}
        lg = m(**enc, use_cache=False).logits[0, -1]
        if max(rooms, key=lambda r: lg[rid[r]].item()) != b[q][1]:
            continue
        items.append(enc)
        n += 1
        if n >= N_ITEMS:
            break
    print(f"  {args.tag}: n items {n} | band L{lo}-{hi}")

    grab['on'] = True
    for L in cap:
        cap[L].clear()
    for enc in items:
        m(**enc, use_cache=False)
    grab['on'] = False

    rows = []
    for L in range(lo, hi + 1):
        X = torch.stack(cap[L]).numpy()                      # (n, hidden)
        for h in range(NH):
            S = X[:, h * HD:(h + 1) * HD]                    # (n, head_dim)
            mu = S.mean(0)
            dev = S - mu                                     # what mean-ablation removes
            nd = np.linalg.norm(dev, axis=1)                 # per item
            ns = np.linalg.norm(S, axis=1)                   # what zero-ablation removes
            rows.append({'layer': L, 'head': h,
                         'mean_norm': float(np.linalg.norm(mu)),
                         'sd_norm': float(nd.mean()),
                         'cv': float(nd.mean() / (np.linalg.norm(mu) + 1e-12)),
                         'displacement_ratio': float((nd / (ns + 1e-12)).mean())})

    dr = np.array([r['displacement_ratio'] for r in rows])
    cv = np.array([r['cv'] for r in rows])
    med = float(np.median(dr))
    world = ('IDENTITY -- mean-ablation barely moves the residual stream' if med < 0.2 else
             'GENTLER -- both interventions move it comparably' if med > 0.5 else
             'NEITHER -- between the pre-registered thresholds')
    print(f"  displacement ratio ||x-mean||/||x|| over {len(rows)} band heads: "
          f"median {med:.3f}  p10 {np.percentile(dr,10):.3f}  p90 {np.percentile(dr,90):.3f}")
    print(f"  cv ||sd||/||mean||:  median {np.median(cv):.3f}  "
          f"p10 {np.percentile(cv,10):.3f}  p90 {np.percentile(cv,90):.3f}")
    print(f"  -> {world}")

    res = {'code_version': _CODE_VERSION, 'code_version': _CODE_VERSION, 'model': args.tag, 'n_items': n, 'band': [lo, hi], 'n_heads_measured': len(rows),
           'displacement_ratio_median': med,
           'displacement_ratio_p10': float(np.percentile(dr, 10)),
           'displacement_ratio_p90': float(np.percentile(dr, 90)),
           'cv_median': float(np.median(cv)),
           'verdict': world.split(' --')[0], 'per_head': rows}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out = f"{args.out}_{args.tag}.json"
    json.dump(res, open(out, 'w'), indent=2, default=float)
    print(f"  -> {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
