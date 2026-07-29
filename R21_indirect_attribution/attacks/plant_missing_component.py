#!/usr/bin/env python3
"""P7 ATTACK ON R21's OWN POSITIVE CONTROL -- a copy of run.py with ONE line changed.

Layer 20's MLP is deleted from the enumeration (`* (0.0 if L == 20 else 1.0)`), which is exactly
what "a component is missing from the sum" means. Run it on any band layer BELOW 20 -- ablating a
head at L27 cannot change layer 20's MLP, so the plant is a no-op there and the first attempt
proved nothing:

    gpu-run ... attacks/plant_missing_component.py --tag plantL14 --layers 14:15

Result, against the honest run on the same 120 items:

    control as published, max|OWN+ATT+MLP+EMB+NORM - total_here|
        honest  1.089e-07      PLANTED 1.275e-07     <- STILL PASSES
    the EMB residue
        honest  8.447e-08      PLANTED 2.398e-02     <- caught, five orders of magnitude
    and the published class number moves unremarked: L14H00 mlp -0.11901 -> -0.11502

D157. The original file (kept below) -- R21 -- attribute the indirect term of I_final to component classes. No mechanism is named.

Registered in R21_indirect_attribution/PREREGISTRATION.md, committed before this file existed.

The final pre-norm residual at the query position is a sum of component writes, and `rms(res)` is a
SCALAR, so for a FIXED comparator the margin is exactly additive:

    margin(res) = k * SUM_c v_c        k = rms(res),  v_c = (u_cor - u_comp).(g (*) w_c)

Ablating head h therefore splits the measured drop into terms that must SUM to it:

    OWN   the ablated head's own write            ATT   every other attention head   (335)
    MLP   every MLP block                  (28)   EMB   embedding + biases + residue
    NORM  the (k' - k) global gain term

The positive control is that identity: OWN+ATT+MLP+EMB+NORM must reproduce R10's frozen total. A
discrepancy is not noise, it is a missing component.
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

sys.path.insert(0, '/home/ivan/AblationNoise')
from task import OBJECTS, PERSONS, ROOMS                                  # noqa: E402

_HERE_F = Path(__file__).resolve()
_ROOT_F = Path('/home/ivan/AblationNoise')
_PRODUCER = 'scratchpad/r21_planted.py'
_CODE_VERSION = __import__('hashlib').sha256(_HERE_F.read_bytes()).hexdigest()[:8]

torch.set_num_threads(20)

N_ITEMS = 120
SEEDS = list(range(3000, 3400))
BAND_LO, BAND_HI = 14, 28


def bindings(seed, rooms=None):
    """Byte-for-byte R10_exhaustive/run.py:76-88."""
    rooms = list(ROOMS) if rooms is None else list(rooms)
    r = random.Random(seed)
    ps, obs = list(PERSONS), list(OBJECTS)
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
    ap.add_argument('--out', default='results/r21_indirect')
    ap.add_argument('--n-items', type=int, default=N_ITEMS)
    ap.add_argument('--layers', default=None, help='LO:HI half-open, for resumable attempts')
    args = ap.parse_args()

    out_path = Path(f'{args.out}_{args.tag}.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ckpt = Path(str(out_path) + '.ckpt')

    def refuse(verdict, why, **extra):
        json.dump({'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag,
                   'verdict': verdict, 'why': why, **extra}, open(out_path, 'w'), indent=2)
        raise SystemExit(f'REFUSED: {why} -> {out_path}')

    R10 = json.load(open(args.total_from))
    rooms = list(R10['rooms'])
    R10L = {int(k): v for k, v in R10['layers'].items()}

    tok = AutoTokenizer.from_pretrained(args.model)
    m = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32,
                                             device_map='cuda')
    m.eval()
    NL, NH = len(m.model.layers), m.config.num_attention_heads
    HD, D = m.config.hidden_size // NH, m.config.hidden_size
    if not getattr(m.config, 'tie_word_embeddings', False):
        refuse('REFUSED-UNTIED-EMBEDDINGS', 'this readout assumes W_U = W_E')

    def content_ids(s):
        return tok.encode(' ' + s, add_special_tokens=False)

    room_ids = {r: content_ids(r) for r in rooms}
    prefix_len = 1 if len({i[0] for i in room_ids.values()}) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[prefix_len] for r, ids in room_ids.items()}
    single = [p for p in PERSONS if len(content_ids(p)) == 1 + prefix_len]

    g = m.model.norm.weight.detach().float()
    eps = getattr(m.model.norm, 'variance_epsilon', 1e-6)
    WE = m.get_input_embeddings().weight.detach().float()
    U = torch.stack([WE[rid[r]] for r in rooms])

    # ---- capture every component's write at the final position.
    # ATTENTION IS CAPTURED AT o_proj's INPUT, NOT ITS OUTPUT, so it can be split per head:
    # W_O z = SUM_h W_O[:, hHD:(h+1)HD] z[hHD:(h+1)HD]. The o_proj BIAS, if any, is not per-head and
    # falls into EMB by construction -- which is why EMB is a measured residue and not asserted zero.
    cache = {}
    ablate = {'L': None, 'h': None}

    def mk_attn_pre(L):
        def pre(mod, a):
            z = a[0].clone()
            if ablate['L'] == L:
                lo = ablate['h'] * HD
                z[0, -1, lo:lo + HD] = 0
            cache[('z', L)] = z[0, -1].detach().float()
            return (z,) + a[1:]
        return pre

    def mk_mlp_post(L):
        def post(mod, a, out):
            cache[('mlp', L)] = out[0, -1].detach().float()
            return out
        return post

    name0, _ = resolve_o_proj(m.model.layers[0])
    WO = []
    for L in range(NL):
        nm, proj = resolve_o_proj(m.model.layers[L])
        if nm != name0:
            refuse('REFUSED-NONUNIFORM-STACK', f'layer {L} exposes {nm}, layer 0 exposes {name0}')
        proj.register_forward_pre_hook(mk_attn_pre(L))
        m.model.layers[L].mlp.register_forward_hook(mk_mlp_post(L))
        WO.append(proj.weight.detach().float())
    m.model.norm.register_forward_pre_hook(
        lambda mod, a: cache.__setitem__(('res',), a[0][0, -1].detach().float()) or a)
    print(f'  hooked {NL} layers: {name0} (pre) + mlp (post) + final norm', flush=True)

    def project(dirv):
        """dirv @ W_O for every layer, computed ONCE per item and reused across all 168 head
        conditions. dirv . (W_O[:, hHD:(h+1)HD] @ z_h) == (dirv @ W_O)[hHD:(h+1)HD] . z_h, so the
        336 small matmuls per item per condition collapse to 28 matvecs per ITEM. Identical
        arithmetic, not an approximation -- checked against the un-optimised version on the smoke
        file before this replaced it."""
        return torch.stack([dirv @ WO[L] for L in range(NL)])          # (NL, D)

    def components(dirv, DW):
        """dirv: (D,) margin direction g*(u_cor - u_comp). DW: (NL, D) = dirv @ W_O per layer."""
        res = cache[('res',)]
        Z = torch.stack([cache[('z', L)] for L in range(NL)])          # (NL, D)
        att = (DW.view(NL, NH, HD) * Z.view(NL, NH, HD)).sum(-1).cpu()  # (NL, NH)
        mlp = torch.stack([torch.dot(dirv, cache[('mlp', L)]) * (0.0 if L == 20 else 1.0)
                           for L in range(NL)]).cpu()   # PLANTED OMISSION: layer 20's MLP
        tot_v = torch.dot(dirv, res)
        emb = float(tot_v - att.sum() - mlp.sum())
        return att, mlp, emb, float(tot_v), res

    band = [(L, h) for L in range(BAND_LO, min(BAND_HI, NL)) for h in range(NH)]
    lo_L, hi_L = (BAND_LO, BAND_HI)
    if args.layers:
        lo_L, hi_L = (int(x) for x in args.layers.split(':'))
    done, acc = set(), {}
    if ckpt.exists():
        c = json.load(open(ckpt))
        if c.get('code_version') == _CODE_VERSION:
            done, acc = set(tuple(x) for x in c['done']), {tuple(json.loads(k)): v
                                                           for k, v in c['acc'].items()}
            print(f'  RESUMING: {len(done)} heads already done', flush=True)

    # collect the item set once (identical filter to R10)
    items = []
    for s in SEEDS:
        b = bindings(s, rooms)
        q = next((p for p in single if p in b), None)
        if q is None:
            continue
        items.append((tok(prompt(q, b), return_tensors='pt'), b[q][1]))
        if len(items) >= args.n_items * 2:
            break

    # clean pass per item: the comparator, k, and the clean component table
    clean = []
    ablate['L'] = None
    n_base = 0
    for enc0, cor in items:
        enc = {k: v.to(m.device) for k, v in enc0.items()}
        cache.clear()
        lg = m(**enc, use_cache=False).logits[0, -1]
        if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
            continue
        ci = rooms.index(cor)
        others = [j for j in range(len(rooms)) if j != ci]
        res = cache[('res',)]
        k = float(torch.rsqrt(res.pow(2).mean() + eps))
        sub = (U @ (res * k * g))
        comp = max(others, key=lambda j: float(sub[j]))
        dirv = g * (U[ci] - U[comp])
        DW = project(dirv)
        att, mlp, emb, tot_v, _ = components(dirv, DW)
        clean.append({'enc': enc, 'ci': ci, 'comp': comp, 'dirv': dirv, 'DW': DW, 'k': k,
                      'att': att, 'mlp': mlp, 'emb': emb, 'tot_v': tot_v,
                      'margin': k * tot_v})
        n_base += 1
        if n_base >= args.n_items:
            break
    if n_base < 30:
        refuse('REFUSED-TOO-FEW-ITEMS', f'only {n_base} items passed the baseline filter')
    print(f'  n={n_base}   base margin {np.mean([c["margin"] for c in clean]):.6f}   '
          f'R10 recorded {R10["base_margin"]:.6f}', flush=True)

    for (L, h) in band:
        if (L, h) in done or not (lo_L <= L < hi_L):
            continue
        s = {'own': 0.0, 'att': 0.0, 'mlp': 0.0, 'emb': 0.0, 'norm': 0.0,
             'att_abs': 0.0, 'mlp_abs': 0.0, 'att_late': 0.0, 'total_measured_here': 0.0}
        ablate['L'], ablate['h'] = L, h
        for c in clean:
            cache.clear()
            m(**c['enc'], use_cache=False)
            att2, mlp2, emb2, tot_v2, res2 = components(c['dirv'], c['DW'])
            k2 = float(torch.rsqrt(res2.pow(2).mean() + eps))
            datt = att2 - c['att']
            dmlp = mlp2 - c['mlp']
            own = float(datt[L, h])
            dattd = datt.clone(); dattd[L, h] = 0.0
            # drop = clean - ablated, so every term is NEGATED relative to the delta
            s['own'] += -k2 * own
            s['att'] += -k2 * float(dattd.sum())
            s['mlp'] += -k2 * float(dmlp.sum())
            s['emb'] += -k2 * (emb2 - c['emb'])
            s['norm'] += -(k2 - c['k']) * c['tot_v']
            s['att_abs'] += k2 * float(dattd.abs().sum())
            s['mlp_abs'] += k2 * float(dmlp.abs().sum())
            s['att_late'] += -k2 * float(dattd[L + 1:].sum())
            s['total_measured_here'] += c['margin'] - k2 * tot_v2
        acc[(L, h)] = {kk: vv / n_base for kk, vv in s.items()}
        acc[(L, h)]['total_r10'] = R10L[L]['per_head'][str(h)]
        done.add((L, h))
        if len(done) % NH == 0:
            tmp = Path(str(ckpt) + '.tmp')
            json.dump({'code_version': _CODE_VERSION,
                       'done': sorted(list(x) for x in done),
                       'acc': {json.dumps(list(kk)): vv for kk, vv in acc.items()}},
                      open(tmp, 'w'))
            tmp.replace(ckpt)
            print(f'  {len(done)}/{len(band)} heads done', flush=True)
    ablate['L'] = None

    json.dump({'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag,
               'verdict': 'MEASURED', 'n_items': n_base, 'n_layers': NL, 'n_heads': NH,
               'band': [BAND_LO, BAND_HI - 1], 'rooms': rooms, 'dtype': 'float32',
               'base_margin': float(np.mean([c['margin'] for c in clean])),
               'r10_base_margin': R10['base_margin'], 'total_source': args.total_from,
               'n_att_members': NL * NH - 1, 'n_mlp_members': NL,
               'cells': {f'L{L:02d}H{h:02d}': acc[(L, h)] for (L, h) in sorted(acc)}},
              open(out_path, 'w'), indent=1)
    print(f'  wrote {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
