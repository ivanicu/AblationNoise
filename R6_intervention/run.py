#!/usr/bin/env python3
"""R6 — IS THE FLOOR A PROPERTY OF ABLATION, OR A PROPERTY OF ZEROING?

Pre-registration: PREREGISTRATION.md, committed before this file existed. Nothing in it is
changed here; where this file makes a choice the pre-registration did not, that choice is marked
`FREE PARAMETER` in a comment and reported in the result file.

Three interventions on the same head slice, at the same final position, over the same items and the
same 30 draws at the same seed:

    zero      write 0                                    -- R1's intervention, unchanged
    mean      write that head's slice averaged over items -- on-distribution, no item information
    resample  write that head's slice from another item   -- on-distribution, WRONG item information

THE ZERO ARM IS NOT A CONTROL, IT IS A REPRODUCTION. It must land within 10% of R1's checked-in
ratio_k1 for the same model. R1's draw order is reproduced exactly (k=1 is the first size in its
sweep, so the first 30 band and first 30 sham draws off Random(DRAW_SEED) are the same objects
whether or not the larger sizes follow). If the zero arm disagrees, the new plumbing changed the old
path and every comparison in the round is between two things that are not what they are labelled.
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
from task import PERSONS, OBJECTS, ROOMS  # noqa: E402

# THE RESULT FILE MUST KNOW WHICH CODE PRODUCED IT. A sibling project recorded this exact defect:
# a fix was announced while the running workers kept executing the pre-edit file, and nothing in
# the output could have shown it. Its durable fix -- stamp sha256(source) into every row -- was
# never carried here, and on 2026-07-28 an audit found 40 result files with zero provenance and
# 12 of them produced by code that has since been edited.
_PRODUCER = __import__("pathlib").Path(__file__).name
_CODE_VERSION = __import__("hashlib").sha256(
    __import__("pathlib").Path(__file__).read_bytes()).hexdigest()[:8]

torch.set_num_threads(20)

K = 1                       # only k=1 -- declared in the pre-registration's cost section
N_DRAWS = 30
N_ITEMS = 120
SEEDS = list(range(3000, 3400))
DRAW_SEED = 20260727        # identical to R1, so the draws are the same head sets
RESAMPLE_SEED = 20260728    # FREE PARAMETER: the partner permutation. Reported in the result file.
INTERVENTIONS = ('zero', 'mean', 'resample')


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
    ap.add_argument('--dtype', default='float32', choices=['float32', 'bfloat16'])
    ap.add_argument('--max-gpu', default='')
    ap.add_argument('--out', default=str(HERE / 'results' / 'r6_intervention'))
    args = ap.parse_args()
    rooms = args.rooms

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    kw = dict(trust_remote_code=True, torch_dtype=getattr(torch, args.dtype),
              attn_implementation='eager')
    if args.max_gpu and torch.cuda.is_available():
        kw.update(device_map='auto', max_memory={0: args.max_gpu, 'cpu': '40GiB'})
    else:
        kw.update(device_map='cuda' if torch.cuda.is_available() else 'cpu')
    m = AutoModelForCausalLM.from_pretrained(args.model, **kw).eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    lo, hi = NL // 2, NL - 1
    sham_lo, sham_hi = 0, max(1, NL // 4)
    PC_LAYER = lo + (hi - lo) // 2      # FREE PARAMETER: which layer the positive control kills.

    from detectors.readout_tokens import check_readout
    rep = check_readout(tok, rooms)
    print(f"  readout detector: {rep.verdict} -- {rep.why}")
    if not rep.ok():
        raise SystemExit(f"REFUSED: {args.tag} readout is {rep.verdict}. {rep.why}")
    rid, pl = rep.scored_ids, rep.shared_prefix_len
    single = [p for p in PERSONS if len(tok.encode(' ' + p, add_special_tokens=False)) == 1 + pl]
    if not single:
        raise SystemExit(f"REFUSED: {args.tag} has no single-token person name.")

    # ── the one hook, in three modes ─────────────────────────────────────────────────────────
    # `capture` records the final-position o_proj INPUT, which is the concatenation of every head's
    # output for this layer. mean and resample are then slices of that same recorded object, so the
    # three interventions differ only in what is written -- never in where or when.
    mode = {'op': 'idle', 'intervention': 'zero', 'item': 0}
    active: dict[int, set[int]] = {}
    cap: dict[int, list[torch.Tensor]] = {L: [] for L in range(NL)}
    meanvec: dict[int, torch.Tensor] = {}
    partner: list[int] = []

    def mk(L):
        def pre(mod, a):
            if mode['op'] == 'capture':
                cap[L].append(a[0][0, -1].detach().float().cpu().clone())
                return a
            if mode['op'] != 'ablate' or L not in active:
                return a
            x = a[0].clone()
            iv = mode['intervention']
            for h in active[L]:
                sl = slice(h * HD, (h + 1) * HD)
                if iv == 'zero':
                    x[0, -1, sl] = 0
                elif iv == 'mean':
                    x[0, -1, sl] = meanvec[L][sl].to(x.dtype).to(x.device)
                else:
                    src = cap[L][partner[mode['item']]]
                    x[0, -1, sl] = src[sl].to(x.dtype).to(x.device)
            return (x,) + a[1:]
        return pre

    name0, _ = resolve_o_proj(m.model.layers[0])
    if name0 is None:
        raise SystemExit(f"REFUSED: cannot find the attention output projection on {args.tag}.")
    for L in range(NL):
        nm, proj = resolve_o_proj(m.model.layers[L])
        if nm != name0:
            raise SystemExit(f"REFUSED: layer {L} exposes {nm}, layer 0 exposes {name0}.")
        proj.register_forward_pre_hook(mk(L))
    print(f"  hooked {NL}/{NL} layers at .{name0}")

    # ── item set: same seeds, same filter, same size as R1 ───────────────────────────────────
    items, base = [], []
    mode['op'] = 'idle'
    for s in SEEDS:
        b = bindings(s, rooms)
        q = next((p for p in single if p in b), None)
        if q is None:
            continue
        enc = {k: v.to(m.device) for k, v in tok(prompt(q, b), return_tensors='pt').items()}
        cor = b[q][1]
        active.clear()
        lg = m(**enc, use_cache=False).logits[0, -1]
        if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
            continue
        base.append(lg[rid[cor]].item() - max(lg[rid[r]].item() for r in rooms if r != cor))
        items.append((enc, cor))
        if len(items) >= N_ITEMS:
            break
    n = len(items)
    if n < 30:
        raise SystemExit(f"REFUSED: {args.tag} answered only {n}/{len(SEEDS)} seeds correctly.")
    bm = float(np.mean(base))
    print(f"  n items {n} | baseline margin {bm:.4f} | band L{lo}-{hi} | sham L{sham_lo}-{sham_hi}")

    # ── the capture pass: one clean forward per item, no ablation ────────────────────────────
    mode['op'] = 'capture'
    for L in cap:
        cap[L].clear()
    for enc, _ in items:
        m(**enc, use_cache=False)
    mode['op'] = 'idle'
    for L in range(NL):
        assert len(cap[L]) == n, f"layer {L} captured {len(cap[L])} of {n}"
        meanvec[L] = torch.stack(cap[L]).mean(0)
    # A derangement: every item is paired with a different one. A fixed cyclic offset is the
    # simplest object with that property and it is fully determined by RESAMPLE_SEED.
    off = 1 + random.Random(RESAMPLE_SEED).randrange(n - 1)
    partner = [(i + off) % n for i in range(n)]
    assert all(partner[i] != i for i in range(n))
    print(f"  captured {NL} layers x {n} items | resample offset {off}")

    # ── the draws: generated exactly as R1 generates them, so k=1 is the same head sets ──────
    rng = random.Random(DRAW_SEED)
    band_pool = [(L, h) for L in range(lo, hi + 1) for h in range(NH)]
    sham_pool = [(L, h) for L in range(sham_lo, sham_hi + 1) for h in range(NH)]
    band_draws = [rng.sample(band_pool, K) for _ in range(N_DRAWS)]
    sham_draws = [rng.sample(sham_pool, min(K, len(sham_pool))) for _ in range(N_DRAWS)]
    pc_heads = [(PC_LAYER, h) for h in range(NH)]

    def sweep(heads, intervention):
        """Mean drop in margin over items, for one head set under one intervention."""
        mode['op'], mode['intervention'] = 'ablate', intervention
        active.clear()
        for (L, h) in heads:
            active.setdefault(L, set()).add(h)
        d = []
        for i, (enc, cor) in enumerate(items):
            mode['item'] = i
            lg = m(**enc, use_cache=False).logits[0, -1]
            d.append(base[i] - (lg[rid[cor]].item()
                                - max(lg[rid[r]].item() for r in rooms if r != cor)))
        active.clear()
        mode['op'] = 'idle'
        return float(np.mean(d))

    arms = {}
    for iv in INTERVENTIONS:
        bandv = np.array([sweep(d, iv) for d in band_draws])
        shamv = np.array([sweep(d, iv) for d in sham_draws])
        pcv = sweep(pc_heads, iv)
        bf = float(bandv.std(ddof=1) / abs(bm))
        sf = float(shamv.std(ddof=1) / abs(bm))
        arms[iv] = {
            'band_floor': bf, 'sham_floor': sf, 'ratio_k1': bf / sf if sf else float('nan'),
            'band_mean': float(bandv.mean()), 'band_sd': float(bandv.std(ddof=1)),
            'sham_mean': float(shamv.mean()), 'sham_sd': float(shamv.std(ddof=1)),
            'band_min': float(bandv.min()), 'band_max': float(bandv.max()),
            'positive_control': pcv, 'pc_layer': PC_LAYER,
            # THE ARM'S OWN POSITIVE CONTROL, per the pre-registration's second invalidating check.
            # An intervention that writes back nearly the true value produces a small, beautiful,
            # meaningless floor -- indistinguishable from a dead instrument without this.
            'pc_clears_own_floor': bool(abs(pcv) > bandv.std(ddof=1)),
            'pc_over_band_sd': float(abs(pcv) / bandv.std(ddof=1)) if bandv.std(ddof=1) else None,
        }
        a = arms[iv]
        print(f"  {iv:<9} band floor {bf:.4f}  sham floor {sf:.4f}  ratio {a['ratio_k1']:6.2f}x"
              f"  | PC {pcv:+.4f} = {a['pc_over_band_sd']:.1f} band-sd "
              f"{'ok' if a['pc_clears_own_floor'] else 'DEAD'}")

    # ── invalidating check 1: the zero arm must reproduce R1 ─────────────────────────────────
    r1p = HERE.parent / 'R1_noise_floor' / 'results' / f'r1v3_atlas_{args.tag}.json'
    repro = {'r1_file': str(r1p.name), 'available': r1p.exists()}
    if r1p.exists():
        c = json.load(open(r1p))['cells']
        r1r = c['band_k1']['floor'] / c['sham_k1']['floor']
        repro.update({'r1_ratio_k1': r1r, 'r6_zero_ratio_k1': arms['zero']['ratio_k1'],
                      'rel_diff': abs(arms['zero']['ratio_k1'] - r1r) / r1r,
                      'reproduces': bool(abs(arms['zero']['ratio_k1'] - r1r) / r1r <= 0.10)})
        print(f"\n  CHECK 1 zero arm vs R1: {r1r:.2f}x vs {arms['zero']['ratio_k1']:.2f}x "
              f"({100*repro['rel_diff']:.1f}% apart) -> "
              f"{'REPRODUCES' if repro['reproduces'] else '*** DOES NOT REPRODUCE ***'}")
    else:
        print(f"\n  CHECK 1 SKIPPED: no R1 result for {args.tag} at {r1p.name}")

    dead = [iv for iv in INTERVENTIONS if not arms[iv]['pc_clears_own_floor']]
    print(f"  CHECK 2 every arm has a live positive control: "
          f"{'PASS' if not dead else 'FAIL on ' + ', '.join(dead)}")

    rr = {iv: arms[iv]['ratio_k1'] / arms['zero']['ratio_k1'] for iv in ('mean', 'resample')}
    af = {iv: arms[iv]['band_floor'] / arms['zero']['band_floor'] for iv in ('mean', 'resample')}
    print(f"\n  rr (ratio of ratios vs zero): " +
          '  '.join(f"{k} {v:.2f}x" for k, v in rr.items()))
    print(f"  af (absolute band floor vs zero): " +
          '  '.join(f"{k} {v:.2f}x" for k, v in af.items()))

    res = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag, 'n_items': n, 'n_draws': N_DRAWS, 'k': K, 'dtype': args.dtype,
           'band': [lo, hi], 'sham_band': [sham_lo, sham_hi], 'rooms': rooms,
           'draw_seed': DRAW_SEED, 'resample_seed': RESAMPLE_SEED, 'resample_offset': off,
           'pc_layer': PC_LAYER, 'base_margin': bm,
           'mean_source': 'in-run, all items, final position',
           'arms': arms, 'rr': rr, 'af': af,
           'check1_zero_reproduces_r1': repro,
           'check2_dead_arms': dead,
           'round_valid': bool(not dead and repro.get('reproduces', False)),
           'informative': bool(arms['zero']['ratio_k1'] > 1.5)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out = f"{args.out}_{args.tag}.json"
    json.dump(res, open(out, 'w'), indent=2, default=float)
    print(f"\n  round_valid {res['round_valid']} | informative {res['informative']}\n  -> {out}")
    return 0 if res['round_valid'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
