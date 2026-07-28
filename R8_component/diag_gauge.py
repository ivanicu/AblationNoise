#!/usr/bin/env python3
"""R8 DIAGNOSTIC — is the norm-matching matched in a basis the MODEL privileges?

THE ATTACK, AND IT IS THE AUTHOR'S OWN. An attention head's output slice z_h feeds W_O,h. For any
invertible A_h, replacing W_V,h -> A_h W_V,h and W_O,h -> W_O,h A_h^{-1} leaves the model's
behaviour identical. That is a real GL(head_dim) gauge freedom, and it decides which of this
repository's measurements are facts about the COMPUTATION and which are facts about the stored
PARAMETERIZATION:

    zero-ablation      z <- 0        0 maps to 0 under any A_h        GAUGE-INVARIANT
    mean-ablation      z <- mu       the mean commutes with A_h        GAUGE-INVARIANT
    resample           z <- z_j      transforms the same way           GAUGE-INVARIANT
    ||x - mu|| / ||x|| (R6 diag)     a NORM in head coordinates        NOT invariant
    R7/R8's matched d                a NORM in head coordinates        NOT invariant

So R1, R2, R5 and R6's arms survive the argument outright. R7's and R8's matching does not: two
displacements of equal norm in head coordinates can differ in the residual stream by up to the
condition number of W_O,h -- median 5.8x, max 17.7x on qwen2.5-1.5b's studied band.

THAT IS A BOUND, NOT A MEASUREMENT, WHICH IS WHY THIS SCRIPT EXISTS. The question is not what the
gauge PERMITS but what the actual displacement directions DO. Measured on 30 items x 168 band
heads, the four arms whose head-coordinate norms are identical to 0.00% agree in residual-stream
norm ||W_O . delta|| to within 1.11x -- far below the 5.8x permitted. The displacement directions
(mu - x, mu, x, random) are generic with respect to W_O's singular structure, so all four scale by
roughly its RMS singular value.

VERDICT: the gauge argument is sound in principle and does not bite on this model. R7's and R8's
ordering is therefore NOT an artifact of residual-norm mismatch -- a control those rounds did not
previously have, and one that costs 30 forward passes on a CPU.

WHAT IT DOES NOT SHOW: this is an aggregate over band heads, and the distribution is heavy-tailed
(mean 1.23 vs median 0.72 for the mean arm). A per-head version could still find individual heads
where the arms are badly mismatched. The ordering claim is also an aggregate, so the two are
matched in scope -- but a per-head readability claim would need the per-head version of this check.

    python3 R8_component/diag_gauge.py --model <hf-path> --tag <name> [--items 30]
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
ARMS = ('mean', 'constant_only', 'shrink', 'randdir')


def bindings(seed, rooms):
    r = random.Random(seed)
    ps, obs = list(PERSONS), list(OBJECTS)
    a = (list(rooms) * 4)[:len(ps)]
    r.shuffle(ps); r.shuffle(obs); r.shuffle(a)
    return {ps[i]: (obs[i], a[i]) for i in range(len(ps))}


def prompt(q, b):
    lines = [f"{p} owns the {b[p][0]}. The {b[p][0]} is in the {b[p][1]} room." for p in PERSONS]
    return '\n'.join(lines + [f"Question: Which room should {q} go to find their object?",
                              "Answer: The"])


@torch.no_grad()
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--items', type=int, default=30)
    ap.add_argument('--rooms', nargs='*', default=['stone', 'iron', 'glass', 'water'])
    ap.add_argument('--out', default=str(HERE / 'results' / 'r8_diag_gauge'))
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        args.model, trust_remote_code=True, torch_dtype=torch.float32,
        device_map='cuda' if torch.cuda.is_available() else 'cpu',
        attn_implementation='eager').eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    lo, hi = NL // 2, NL - 1

    cap: dict[int, list[torch.Tensor]] = {L: [] for L in range(NL)}

    def mk(L):
        def pre(mod, a):
            cap[L].append(a[0][0, -1].detach().float().cpu().clone())
            return a
        return pre

    for L in range(NL):
        att = getattr(m.model.layers[L], 'self_attn', None) or m.model.layers[L].attention
        proj = getattr(att, 'o_proj', None) or getattr(att, 'wo')
        proj.register_forward_pre_hook(mk(L))

    single = [p for p in PERSONS if len(tok.encode(' ' + p, add_special_tokens=False)) == 1]
    n = 0
    for s in range(3000, 3400):
        b = bindings(s, args.rooms)
        q = next((p for p in single if p in b), None)
        if q is None:
            continue
        enc = {k: v.to(m.device) for k, v in tok(prompt(q, b), return_tensors='pt').items()}
        m(**enc, use_cache=False)
        n += 1
        if n >= args.items:
            break

    g = torch.Generator().manual_seed(1)
    res = {k: [] for k in ARMS}
    cond = []
    for L in range(lo, hi + 1):
        X = torch.stack(cap[L]).view(n, NH, HD)
        MU = X.mean(0)
        att = getattr(m.model.layers[L], 'self_attn', None) or m.model.layers[L].attention
        WO = (getattr(att, 'o_proj', None) or getattr(att, 'wo')).weight.float().cpu()
        for h in range(NH):
            B = WO[:, h * HD:(h + 1) * HD]
            sv = torch.linalg.svdvals(B)
            cond.append(float(sv[0] / sv[-1]))
            mu = MU[h]
            mun = mu.norm().clamp_min(1e-9)
            for i in range(n):
                x = X[i, h]
                d = (x - mu).norm()
                xn = x.norm().clamp_min(1e-9)
                u = torch.randn(HD, generator=g)
                u = u / u.norm()
                for k, dd in (('mean', mu - x), ('constant_only', -(d / mun) * mu),
                              ('shrink', -(d / xn) * x), ('randdir', d * u)):
                    res[k].append(float((B @ dd).norm()))

    means = {k: float(np.mean(v)) for k, v in res.items()}
    meds = {k: float(np.median(v)) for k, v in res.items()}
    spread = max(means.values()) / min(means.values())
    permitted = float(np.median(cond))
    print(f"  {args.tag}: {n} items x {len(cond)} band heads")
    print(f"  head-coordinate norms are identical by construction (R7/R8 CHECK 1 = 0.00%)")
    for k in ARMS:
        print(f"    {k:<14} ||W_O.delta|| mean {means[k]:8.4f}  median {meds[k]:8.4f}"
              f"  vs mean-arm {means[k]/means['mean']:5.2f}x")
    print(f"  SPREAD in the residual stream: {spread:.2f}x")
    print(f"  PERMITTED by the gauge (median cond(W_O,h)): {permitted:.1f}x")
    print(f"  -> {'matching survives the basis change' if spread < 1.5 else 'MATCHING IS BASIS-DEPENDENT'}")

    out = {'code_version': _CODE_VERSION, 'code_version': _CODE_VERSION, 'model': args.tag, 'n_items': n, 'n_band_heads': len(cond),
           'residual_norm_mean': means, 'residual_norm_median': meds,
           'residual_spread': spread, 'permitted_by_gauge_median_cond': permitted,
           'cond_max': float(max(cond)),
           'verdict': 'GAUGE-ROBUST-IN-PRACTICE' if spread < 1.5 else 'BASIS-DEPENDENT'}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    p = f"{args.out}_{args.tag}.json"
    json.dump(out, open(p, 'w'), indent=2, default=float)
    print(f"  -> {p}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
