#!/usr/bin/env python3
"""Control 1 of R28, in float64 on CPU. The rule is unchanged; the INSTRUMENT's noise floor is raised.

Control 1 failed twice in float32, and the emitted sequences said why: the relative error falls as alpha
until roundoff takes over, then rises. At alpha = 1/32 a margin difference is order 1e-3 against a margin
of 4.5, so float32's ~7 significant digits leave roughly 1e-1 relative precision on the difference. The
floor is a property of the dtype, not of the gradient.

So this is NOT another threshold amendment -- AMENDMENT_1's rule is used verbatim, min-over-alpha
relative error <= 1% and halving ratios inside [1.6, 2.4] before each cell's argmin. What changes is that
the difference and the gradient are both computed in float64, where the roundoff floor is ~9 orders of
magnitude lower and cannot masquerade as a failure of the derivative.

The scans themselves stay float32 -- the target must remain the object R10 measured. This model is loaded
for the CONTROL only, and the control is a question about calculus, not about the checkpoint's behaviour.
"""
import argparse
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'R10_exhaustive'))

ALPHAS = (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125)
CTRL1_REL = 0.01
CTRL1_RATIO_LO, CTRL1_RATIO_HI = 1.6, 2.4
N_ITEMS_CTRL = 4
TARGETS = {'qwen2.5-1.5b': ('artifacts/model_qwen2.5-1.5b-instruct',
                            'R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json')}


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import run as R10                                                    # noqa: N813
    from task import PERSONS, ROOMS

    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    args = ap.parse_args()
    md, rf = TARGETS[args.tag]
    ref = json.load(open(REPO / rf))
    rooms = ref['rooms'] if ref.get('rooms') else list(ROOMS)

    tok = AutoTokenizer.from_pretrained(str(REPO / md), trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        str(REPO / md), trust_remote_code=True, dtype=torch.float64,
        attn_implementation='eager', device_map='cpu').eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    print(f'  float64 on CPU   layers {NL}   heads {NH}   dtype '
          f'{next(m.parameters()).dtype}', flush=True)

    def content_ids(s):
        return tok.encode(' ' + s, add_special_tokens=False)
    room_ids = {r: content_ids(r) for r in rooms}
    firsts = {ids[0] for ids in room_ids.values()}
    plen = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[plen] for r, ids in room_ids.items()}
    single = [p for p in PERSONS if len(content_ids(p)) == 1 + plen]

    T, SCALE = {}, {}

    def mk(L, mod):
        def pre(_mod, inp):
            t = inp[0]
            if SCALE:
                t = t.clone()
                for (LL, h), f in SCALE.items():
                    if LL == L:
                        t[..., -1, h * HD:(h + 1) * HD] *= f
                return (t,) + inp[1:]
            if t.requires_grad:
                T[L] = t
            return None
        return mod.register_forward_pre_hook(pre)

    hooks = [mk(L, m.model.layers[L].self_attn.o_proj) for L in range(NL)]

    def margin_of(enc, cor):
        lg = m(**enc, use_cache=False).logits[0, -1]
        return lg[rid[cor]] - max(lg[rid[r]] for r in rooms if r != cor)

    items = []
    with torch.no_grad():
        for s in R10.SEEDS:
            b = R10.bindings(s, rooms)
            q = next((p for p in single if p in b), None)
            if q is None:
                continue
            enc = {k: v for k, v in tok(R10.prompt(q, b), return_tensors='pt').items()}
            cor = b[q][1]
            SCALE.clear()
            lg = m(**enc, use_cache=False).logits[0, -1]
            if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
                continue
            items.append((enc, cor, float(lg[rid[cor]]
                                          - max(lg[rid[r]] for r in rooms if r != cor))))
            if len(items) >= N_ITEMS_CTRL:
                break
    print(f'  control items {len(items)}', flush=True)

    picks = [(L, h) for L in (NL // 3, 2 * NL // 3) for h in range(4)]
    want = {}
    for it, (enc, cor, _bm) in enumerate(items):
        SCALE.clear(); T.clear()
        mg = margin_of(enc, cor)
        order = sorted(T)
        gs = torch.autograd.grad(mg, [T[L] for L in order])
        for L, gt in zip(order, gs):
            av = T[L][0, -1].detach().view(NH, HD)
            gv = gt[0, -1].detach().view(NH, HD)
            d = (av * gv).sum(1)
            for h in range(NH):
                if (L, h) in picks:
                    want[(L, h, it)] = float(d[h])
    print('  gradients computed; sweeping alpha', flush=True)

    c1, ok = {}, True
    with torch.no_grad():
        for (L, h) in picks:
            errs = []
            for it, (enc, cor, bm) in enumerate(items):
                w = want[(L, h, it)]
                seq = []
                for al in ALPHAS:
                    SCALE.clear(); SCALE[(L, h)] = 1.0 - al
                    seq.append((bm - float(margin_of(enc, cor))) / al)
                SCALE.clear()
                rel = [abs(v - w) / max(abs(w), 1e-300) for v in seq]
                jm = min(range(len(rel)), key=lambda j: rel[j])
                ratios = [rel[j] / rel[j + 1] for j in range(jm) if rel[j + 1] > 0]
                band = all(CTRL1_RATIO_LO <= r <= CTRL1_RATIO_HI for r in ratios) if ratios else False
                errs.append({'item': it, 'want': w, 'seq': seq, 'rel_err_seq': rel,
                             'rel_err_min': rel[jm], 'argmin_alpha': ALPHAS[jm],
                             'halving_ratios_before_argmin': ratios, 'ratios_in_band': band})
            wm = max(e['rel_err_min'] for e in errs)
            ab = all(e['ratios_in_band'] for e in errs)
            good = wm <= CTRL1_REL and ab
            ok = ok and good
            c1[f'L{L:02d}H{h:02d}'] = {'worst_rel_err_min': wm, 'ratios_in_band': ab,
                                       'pass': good, 'detail': errs}
            print(f'    L{L:02d}H{h:02d}  worst min-rel-err {wm:.3e}  argmin alphas '
                  f'{[e["argmin_alpha"] for e in errs]}  band {ab}  '
                  f'-> {"PASS" if good else "FAIL"}', flush=True)
    for hk in hooks:
        hk.remove()

    out = {'model': args.tag, 'dtype': 'float64', 'device': 'cpu', 'alphas': list(ALPHAS),
           'rule': 'AMENDMENT_1 verbatim: min-over-alpha rel err <= 0.01 and halving ratios in '
                   '[1.6, 2.4] before the argmin',
           'n_control_items': len(items), 'per_cell': c1, 'pass': ok}
    print(f'\n  CONTROL 1 in float64: {"PASS" if ok else "FAIL"}', flush=True)
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / f'r28_gate1_fd64_{args.tag}.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0 if ok else 3


if __name__ == '__main__':
    sys.exit(main())
