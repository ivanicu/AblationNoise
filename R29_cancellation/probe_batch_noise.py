#!/usr/bin/env python3
"""How much does batching alone move a per-head mean? Measured over a stratified sample of cells.

The I_all positive control failed at a worst |delta mean| of 2.369e-05 against a registered 1e-5. That
worst is taken over 336 cells while the tolerance was a single fixed bound, which is the same defect the
sem tolerance had: a max over a heterogeneous population judged against a number that does not account
for the max.

R18 ran ONE ITEM AT A TIME. So the comparison the control makes is batch-versus-no-batch, and the noise
scale is the spread between chunk=1 and the production chunk -- for MANY cells, not one. A single cell gave
9.045e-06; a max over 336 draws from a 9e-6 scale lands near 3 sigma, about 2.7e-5, which is where the
failure sits. This measures the distribution so a tolerance can be stated against it instead of guessed.

TWO SUPPORTS, because the whole point is that they differ: I_final perturbs one position and I_all
perturbs 121, so the arithmetic downstream of the intervention differs by two orders of magnitude in
extent. Emitting both makes "one tolerance for both supports" checkable rather than assumed.

NO TOLERANCE IS CHOSEN HERE. This file emits a distribution.
"""
import argparse
import json
import math
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'R10_exhaustive'))

PROD_CHUNK = 40
N_PER_LAYER = 2


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import run as R10                                                    # noqa: N813
    from task import PERSONS, ROOMS

    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    ap.add_argument('--layer-stride', type=int, default=4)
    args = ap.parse_args()
    rooms = list(ROOMS)

    tok = AutoTokenizer.from_pretrained(str(REPO / args.model), trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        str(REPO / args.model), trust_remote_code=True, dtype=torch.float32,
        attn_implementation='eager',
        device_map='cuda' if torch.cuda.is_available() else 'cpu').eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH

    def cid(s):
        return tok.encode(' ' + s, add_special_tokens=False)
    room_ids = {r: cid(r) for r in rooms}
    firsts = {ids[0] for ids in room_ids.values()}
    plen = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[plen] for r, ids in room_ids.items()}
    single = [p for p in PERSONS if len(cid(p)) == 1 + plen]

    ACT, MODE = {}, {'support': 'I_final'}

    def mk(L, mod):
        def pre(_mod, inp):
            hs = inp[0]
            if L in ACT and ACT[L]:
                hs = hs.clone()
                for h in ACT[L]:
                    if MODE['support'] == 'I_final':
                        hs[:, -1, h * HD:(h + 1) * HD] = 0
                    else:
                        hs[:, :, h * HD:(h + 1) * HD] = 0
                return (hs,) + inp[1:]
            return None
        return mod.register_forward_pre_hook(pre)

    hooks = [mk(L, m.model.layers[L].self_attn.o_proj) for L in range(NL)]

    def logits(e):
        return m.lm_head(m.model(**e).last_hidden_state[:, -1])

    texts, cors = [], []
    with torch.no_grad():
        for s in R10.SEEDS:
            b = R10.bindings(s, rooms)
            q = next((p for p in single if p in b), None)
            if q is None:
                continue
            e = {k: v.to(m.device) for k, v in tok(R10.prompt(q, b), return_tensors='pt').items()}
            ACT.clear()
            lg = logits(e)[0]
            cor = b[q][1]
            if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
                continue
            texts.append(R10.prompt(q, b))
            cors.append(cor)
            if len(texts) >= 120:
                break
    enc = {k: v.to(m.device) for k, v in tok(texts, return_tensors='pt').items()}
    n = len(texts)
    ci = torch.tensor([rid[c] for c in cors], device=m.device)
    oi = torch.tensor([[rid[r] for r in rooms if r != c] for c in cors], device=m.device)

    def mean_at(chunk):
        acc = []
        for lo in range(0, n, chunk):
            hi = min(lo + chunk, n)
            e = {k: v[lo:hi] for k, v in enc.items()}
            lg = logits(e)
            c = lg.gather(1, ci[lo:hi, None]).squeeze(1)
            o = lg.gather(1, oi[lo:hi]).max(1).values
            acc.append((c - o).float())
        return torch.cat(acc)

    picks = [(L, h) for L in range(0, NL, args.layer_stride) for h in range(N_PER_LAYER)]
    out = {'model': args.tag, 'n_items': n, 'prod_chunk': PROD_CHUNK,
           'n_cells_probed': len(picks), 'supports': {}}
    print(f'  {args.tag}: {len(picks)} cells, chunk 1 vs {PROD_CHUNK}, {n} items', flush=True)
    with torch.no_grad():
        for support in ('I_final', 'I_all'):
            MODE['support'] = support
            ACT.clear()
            b1, b40 = mean_at(1), mean_at(PROD_CHUNK)
            rows = {}
            for (L, h) in picks:
                ACT.clear(); ACT[L] = {h}
                d1 = float((b1 - mean_at(1)).mean())
                d40 = float((b40 - mean_at(PROD_CHUNK)).mean())
                rows[f'L{L:02d}H{h:02d}'] = {'mean_chunk1': d1, 'mean_chunk40': d40,
                                             'abs_diff': abs(d1 - d40)}
            ACT.clear()
            ds = sorted(v['abs_diff'] for v in rows.values())
            out['supports'][support] = {
                'per_cell': rows, 'median': st.median(ds), 'max': ds[-1], 'min': ds[0],
                'p90': ds[max(0, int(0.9 * len(ds)) - 1)],
                'mean': sum(ds) / len(ds),
                'sd': math.sqrt(sum((x - sum(ds) / len(ds)) ** 2 for x in ds) / (len(ds) - 1))
                if len(ds) > 2 else float('nan'),
                'base_abs_diff': abs(float(b1.mean()) - float(b40.mean()))}
            s = out['supports'][support]
            print(f'    {support:<8} |mean(chunk1) - mean(chunk{PROD_CHUNK})| over '
                  f'{len(ds)} cells: median {s["median"]:.3e}  p90 {s["p90"]:.3e}  '
                  f'max {s["max"]:.3e}  sd {s["sd"]:.3e}', flush=True)
            print(f'    {"":<8} base pass alone: {s["base_abs_diff"]:.3e}', flush=True)
    for hk in hooks:
        hk.remove()
    r = out['supports']
    if 'I_final' in r and 'I_all' in r:
        out['i_all_over_i_final_median_ratio'] = r['I_all']['median'] / r['I_final']['median']
        print(f'\n  I_all / I_final median ratio: '
              f'{out["i_all_over_i_final_median_ratio"]:.2f}x   '
              f'(one tolerance for both supports is testable against this)', flush=True)
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / f'r29_batch_noise_{args.tag}.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
