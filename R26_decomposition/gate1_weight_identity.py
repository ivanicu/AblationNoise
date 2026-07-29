#!/usr/bin/env python3
"""Gate 1 of R26_decomposition/PREREGISTRATION.md. Nothing downstream runs until this passes.

The checkpoints were re-downloaded from HuggingFace today; the copies the scans measured are gone.
R6_intervention froze per-head W_O singular summaries for all 168 band heads of qwen2.5-1.5b back when
a local copy existed, explicitly so `make verify` would never need weights. That frozen file is now
something better: a reference for the DOWNLOADED TENSOR BYTES, independent of tokenizer, prompt,
sampling and every other thing that could differ between then and now.

Match to 6 significant figures or stop and report the revision hashes. A mismatch means the artifact
on the Hub is not the artifact the twenty-five rounds measured, and every number in the repository
would be describing a different object than the one about to be measured.

THE GATE IS A HARD RETURN. It is not an `if False:`.
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SIGFIG = 6
REF = REPO / 'R6_intervention' / 'results' / 'wo_block_conditioning_qwen2.5-1.5b.json'
MODEL = REPO / 'artifacts' / 'model_qwen2.5-1.5b-instruct'


def sig_equal(a, b, sig=SIGFIG):
    """Equal to `sig` significant figures. Relative, so it is scale-free across smax and srank."""
    if a == b:
        return True
    if a == 0 or b == 0:
        return False
    return abs(a - b) / max(abs(a), abs(b)) < 10.0 ** (-(sig - 1))


def main():
    import torch
    from safetensors.torch import safe_open

    ref = json.load(open(REF))
    hd = ref['head_dim']
    lo, hi = ref['band']
    print(f'  reference {REF.name}: {ref["n_heads"]} heads, band L{lo}-L{hi}, head_dim {hd}')
    print(f'  producer  {ref["producer"]}')

    shards = sorted(MODEL.glob('*.safetensors'))
    if not shards:
        print('  -> STOP: no safetensors in', MODEL)
        return 3
    index = {}
    for sh in shards:
        with safe_open(sh, framework='pt') as f:
            for k in f.keys():
                index[k] = sh
    print(f'  checkpoint {len(shards)} shard(s), {len(index)} tensors')

    got = {}
    for lay in range(lo, hi + 1):
        key = f'model.layers.{lay}.self_attn.o_proj.weight'
        if key not in index:
            print('  -> STOP: missing', key)
            return 3
        with safe_open(index[key], framework='pt') as f:
            W = f.get_tensor(key).to(torch.float32)
        nh = W.shape[1] // hd
        for h in range(nh):
            blk = W[:, h * hd:(h + 1) * hd]
            s = torch.linalg.svdvals(blk).to(torch.float64)
            smax, smin = float(s[0]), float(s[-1])
            got[(lay, h)] = {'smax': smax, 'smin': smin, 'cond': smax / smin,
                             'srank': float(s.sum() ** 2 / (s * s).sum())}

    fields = ('smax', 'smin', 'cond', 'srank')
    bad, checked = [], 0
    worst = {k: (0.0, None) for k in fields}
    for row in ref['per_head']:
        k = (row['layer'], row['head'])
        if k not in got:
            bad.append((k, 'missing', None, None))
            continue
        for fl in fields:
            checked += 1
            a, b = row[fl], got[k][fl]
            rel = abs(a - b) / max(abs(a), abs(b)) if max(abs(a), abs(b)) > 0 else 0.0
            if rel > worst[fl][0]:
                worst[fl] = (rel, k)
            if not sig_equal(a, b):
                bad.append((k, fl, a, b))

    print(f'\n  compared {checked} values across {len(ref["per_head"])} heads x {len(fields)} fields')
    for fl in fields:
        r, k = worst[fl]
        print(f'    worst relative deviation  {fl:<6} {r:.3e}  at L{k[0]}H{k[1]}'
              if k else f'    {fl}: n/a')
    out = {'reference': str(REF.relative_to(REPO)), 'sigfig': SIGFIG,
           'n_heads_compared': len(ref['per_head']), 'n_values_compared': checked,
           'n_mismatches': len(bad),
           'worst_relative_deviation': {f: worst[f][0] for f in fields},
           'pass': not bad}
    if bad:
        print(f'\n  -> STOP. {len(bad)} mismatch(es) beyond {SIGFIG} significant figures.')
        for k, fl, a, b in bad[:10]:
            print(f'     L{k[0]}H{k[1]} {fl}: frozen {a!r}  recomputed {b!r}')
        out['examples'] = [{'layer': k[0], 'head': k[1], 'field': fl, 'frozen': a,
                            'recomputed': b} for k, fl, a, b in bad[:20]]
    else:
        print(f'\n  -> GATE 1 PASS. Every one of {checked} values agrees to {SIGFIG} significant '
              f'figures. The downloaded bytes are the bytes the scans measured.')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    json.dump(out, open(HERE / 'results' / 'r26_gate1_weight_identity.json', 'w'), indent=1)
    return 0 if not bad else 3


if __name__ == '__main__':
    sys.exit(main())
