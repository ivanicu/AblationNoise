#!/usr/bin/env python3
"""R20 -- decompose I_final into the head's DIRECT path and the rest of the network's response.

Registered in R20_direct_indirect/PREREGISTRATION.md, committed before this file existed.

    total(h)    = the measured I_final drop, read from R10's frozen result -- NOT recomputed here
    direct(h)   = deleting h's write from the FINAL pre-norm residual, nothing else recomputed
    indirect(h) = total - direct

The whole experiment is ONE clean forward pass per item. No ablation is run: every head's write at
the final position is captured in the same pass, and the readout is re-evaluated 336 times per item
in closed form on the cached residual.

THE POSITIVE CONTROL IS THE REASON THIS IS TRUSTWORTHY AND IT IS FREE. Layer 27 has nothing
downstream of it, so `direct_renorm` for its 12 heads must equal R10's measured `total` to numerical
precision. A decomposition that cannot reproduce the case where it must be exact is not measuring a
decomposition.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from task import PERSONS, ROOMS                                          # noqa: E402

_HERE_F = Path(__file__).resolve()
_ROOT_F = next(p for p in _HERE_F.parents if (p / 'Makefile').exists())
_PRODUCER = str(_HERE_F.relative_to(_ROOT_F))
_CODE_VERSION = __import__('hashlib').sha256(_HERE_F.read_bytes()).hexdigest()[:8]

torch.set_num_threads(20)

# IDENTICAL TO R10. Not "similar" -- the total effects are read from R10's frozen file, so a
# different item set would compare two different experiments. R10_exhaustive/run.py:71-73.
N_ITEMS = 120
SEEDS = list(range(3000, 3400))
BAND_LO, BAND_HI = 14, 28
SMALL_DIRECT = 0.01        # registered: heads below this are reported separately, not folded in


def bindings(seed, rooms=None):
    """Byte-for-byte R10_exhaustive/run.py:76-88."""
    rooms = list(ROOMS) if rooms is None else list(rooms)
    r = random.Random(seed)
    ps, obs = list(PERSONS), list(__import__('task').OBJECTS)
    assigned = (rooms * 4)[:len(ps)]
    r.shuffle(ps); r.shuffle(obs); r.shuffle(assigned)
    return {ps[i]: (obs[i], assigned[i]) for i in range(len(ps))}


def prompt(query, b):
    """Byte-for-byte R10_exhaustive/run.py:91-95."""
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
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--total-from',
                    default='R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json')
    ap.add_argument('--out', default='results/r20_direct_indirect')
    ap.add_argument('--n-items', type=int, default=N_ITEMS)
    args = ap.parse_args()

    out_path = Path(f'{args.out}_{args.tag}.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def refuse(verdict, why, **extra):
        json.dump({'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag,
                   'verdict': verdict, 'why': why, **extra}, open(out_path, 'w'), indent=2)
        raise SystemExit(f'REFUSED: {why} -> {out_path}')

    tot_f = Path(args.total_from)
    if not tot_f.exists():
        refuse('REFUSED-NO-TOTALS', f'{tot_f} not found; total(h) is READ, never recomputed here')
    R10 = json.load(open(tot_f))
    rooms = list(R10['rooms'])
    R10L = {int(k): v for k, v in R10['layers'].items()}

    tok = AutoTokenizer.from_pretrained(args.model)
    m = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32,
                                             device_map='cuda')
    m.eval()
    NL = len(m.model.layers)
    NH = m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    D = m.config.hidden_size
    if (NL, NH) != (R10['n_layers'], R10['n_heads']):
        refuse('REFUSED-SHAPE-MISMATCH',
               f'model is {NL}x{NH}, R10 recorded {R10["n_layers"]}x{R10["n_heads"]}')

    def content_ids(s):
        return tok.encode(' ' + s, add_special_tokens=False)

    room_ids = {r: content_ids(r) for r in rooms}
    firsts = {ids[0] for ids in room_ids.values()}
    prefix_len = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[prefix_len] for r, ids in room_ids.items()}
    if len(set(rid.values())) != len(rid):
        refuse('REFUSED-COLLIDING-READOUT', f'room readout tokens collide: {rid}')
    single = [p for p in PERSONS if len(content_ids(p)) == 1 + prefix_len]
    if not single:
        refuse('REFUSED-NO-QUERY-NAMES', 'no single-token person name on this tokenizer')

    # ---- the readout, in closed form on the final pre-norm residual.
    # W_U = W_E (tie_word_embeddings), and the final RMSNorm scale `g` is part of the basis -- D113
    # established that omitting it computes the circuit in the wrong basis.
    if not getattr(m.config, 'tie_word_embeddings', False):
        refuse('REFUSED-UNTIED-EMBEDDINGS',
               'this readout assumes W_U = W_E; the model reports untied embeddings')
    g = m.model.norm.weight.detach().float()                       # (D,)
    eps = getattr(m.model.norm, 'variance_epsilon', 1e-6)
    WE = m.get_input_embeddings().weight.detach().float()          # (V, D)
    U = torch.stack([WE[rid[r]] for r in rooms])                   # (4, D) rows in `rooms` order

    def readout(res):
        """res: (D,) final pre-norm residual -> (4,) logits over the rooms, EXACT."""
        rms = torch.rsqrt(res.pow(2).mean() + eps)
        return U @ (res * rms * g)

    def readout_fixed_scale(res, rms):
        return U @ (res * rms * g)

    # ---- capture: every head's write at the final position, plus the final residual.
    cache = {}

    def mk_pre(L):
        def pre(mod, a):
            cache[('z', L)] = a[0][0, -1].detach().float()          # o_proj INPUT, final position
            return a
        return pre

    name0, _ = resolve_o_proj(m.model.layers[0])
    if name0 is None:
        refuse('REFUSED-NO-O-PROJ', 'cannot find the attention output projection')
    WO = []
    for L in range(NL):
        nm, proj = resolve_o_proj(m.model.layers[L])
        if nm != name0:
            refuse('REFUSED-NONUNIFORM-STACK', f'layer {L} exposes {nm}, layer 0 exposes {name0}')
        proj.register_forward_pre_hook(mk_pre(L))
        WO.append(proj.weight.detach().float())                     # (D, D)
    m.model.norm.register_forward_pre_hook(
        lambda mod, a: cache.__setitem__(('res',), a[0][0, -1].detach().float()) or a)
    # THE REGISTERED LAYER-27 CONTROL WAS BUILT ON A FALSE PREMISE AND FAILED, 18x OVER ITS LIMIT.
    # "The last layer has nothing downstream" is wrong: a decoder block is
    #     h = h + attn(ln1(h));  h = h + mlp(ln2(h))
    # so layer L's attention is followed by layer L's OWN MLP. There is no head anywhere in the
    # stack with zero downstream computation, and the control as registered could never have passed.
    # It is repaired rather than dropped: for the LAST layer only, re-running that one MLP on the
    # modified residual makes the comparison exact again, because nothing but the final norm follows
    # it. This hook captures the residual entering that MLP's layernorm.
    m.model.layers[NL - 1].post_attention_layernorm.register_forward_pre_hook(
        lambda mod, a: cache.__setitem__(('pre_mlp',), a[0][0, -1].detach().float()) or a)
    LAST = m.model.layers[NL - 1]
    print(f'  hooked {NL} layers at .{name0} + the final norm   NH={NH} HD={HD} D={D}')

    heads = [(L, h) for L in range(NL) for h in range(NH)]
    acc = {k: {'dl': 0.0, 'dr': 0.0, 'dm': 0.0, 'dm_recomp': 0.0, 'n': 0, 'flip': 0}
           for k in heads}
    base_margins = []
    n = 0
    for s in SEEDS:
        b = bindings(s, rooms)
        q = next((p for p in single if p in b), None)
        if q is None:
            continue
        enc = {k: v.to(m.device) for k, v in tok(prompt(q, b), return_tensors='pt').items()}
        cor = b[q][1]
        ci = rooms.index(cor)
        cache.clear()
        lg = m(**enc, use_cache=False).logits[0, -1]
        if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
            continue                                    # R10's baseline-correct filter, identical
        res = cache[('res',)]
        clean = readout(res)
        # THE CLOSED-FORM READOUT MUST REPRODUCE THE MODEL'S OWN LOGITS. If it does not, every
        # `direct` below is computed by a readout that is not this model's readout.
        gap = float((clean - torch.stack([lg[rid[r]] for r in rooms]).float()).abs().max())
        if gap > 1e-2:
            refuse('REFUSED-READOUT-MISMATCH',
                   f'closed-form readout differs from the model logits by {gap:.4g}')
        others = [j for j in range(len(rooms)) if j != ci]
        comp = max(others, key=lambda j: float(clean[j]))          # the CLEAN comparator, held fixed
        bm = float(clean[ci] - clean[comp])
        base_margins.append(bm)
        rms_clean = float(torch.rsqrt(res.pow(2).mean() + eps))
        # A CAPTURE HOOK FIRES AGAIN WHEN YOU RE-INVOKE THE MODULE TO ANALYSE IT. The last block's
        # post_attention_layernorm carries the pre-MLP capture hook, and the control below calls
        # that very layernorm 12 times -- so from the second head onward `cache[('pre_mlp',)]` held
        # the PREVIOUS head's modified residual, and each head subtracted from an already-damaged
        # vector. The signature was unmistakable once the per-head errors were printed: head 0 exact
        # at 0.0034, head 1 near, then every later head pinned around 0.6. Read it out ONCE.
        pm = cache[('pre_mlp',)].clone()
        for (L, h) in heads:
            a = WO[L][:, h * HD:(h + 1) * HD] @ cache[('z', L)][h * HD:(h + 1) * HD]
            r2 = res - a
            lin = readout_fixed_scale(r2, rms_clean)
            ren = readout(r2)
            acc[(L, h)]['dl'] += bm - float(lin[ci] - lin[comp])
            acc[(L, h)]['dr'] += bm - float(ren[ci] - ren[comp])
            acc[(L, h)]['n'] += 1
            # comparator disagreement: does the argmax over the other three move?
            if max(others, key=lambda j: float(ren[j])) != comp:
                acc[(L, h)]['flip'] += 1
            if L == NL - 1:
                # exact for the last layer: remove the write, re-run this block's own MLP, read out
                r3 = pm - a
                r3 = r3 + LAST.mlp(LAST.post_attention_layernorm(r3[None, None]))[0, 0].float()
                w = readout(r3)
                acc[(L, h)]['dm'] += bm - float(w[ci] - w[comp])
                # ...AND THE CONTROL MUST USE R10'S OWN MARGIN DEFINITION, NOT MINE. R10 recomputes
                # `max over the other three rooms` after every ablation; the decomposition above
                # holds the CLEAN comparator fixed on purpose, so the two disagree exactly where the
                # argmax moves. That is the fourth confound registered before the run, and it names
                # its own witness: L27H02 has a 0.25 comparator-flip rate, the highest of the twelve,
                # and was the single head still failing the control at 0.3249 while the other eleven
                # sat under 0.031.
                cj = max(others, key=lambda j: float(w[j]))
                acc[(L, h)]['dm_recomp'] += bm - float(w[ci] - w[cj])
        n += 1
        if n >= args.n_items:
            break
    if n < 30:
        refuse('REFUSED-TOO-FEW-ITEMS', f'only {n} items passed the baseline filter (need 30)')

    base_margin = float(np.mean(base_margins))
    print(f'  n={n}   base margin {base_margin:.6f}   R10 recorded {R10["base_margin"]:.6f}')

    cells = {}
    for (L, h) in heads:
        a = acc[(L, h)]
        cells[f'L{L:02d}H{h:02d}'] = {
            'direct_linear': a['dl'] / a['n'],
            'direct_renorm': a['dr'] / a['n'],
            'total': R10L[L]['per_head'][str(h)],
            'direct_plus_own_mlp': (a['dm'] / a['n']) if L == NL - 1 else None,
            'direct_plus_own_mlp_recomp': (a['dm_recomp'] / a['n']) if L == NL - 1 else None,
            'comparator_flip_rate': a['flip'] / a['n']}
    for k, c in cells.items():
        c['indirect'] = c['total'] - c['direct_renorm']

    json.dump({'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag,
               'verdict': 'MEASURED', 'n_items': n, 'n_layers': NL, 'n_heads': NH,
               'band': [BAND_LO, BAND_HI - 1], 'rooms': rooms, 'dtype': 'float32',
               'base_margin': base_margin, 'r10_base_margin': R10['base_margin'],
               'total_source': str(tot_f), 'small_direct_threshold': SMALL_DIRECT,
               'cells': cells}, open(out_path, 'w'), indent=1)
    print(f'  wrote {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
