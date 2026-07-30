#!/usr/bin/env python3
"""Control 1 on the ESTIMAND, per AMENDMENT_2. float64 CPU, all 120 items, batched.

kappa is built from P = log|mean_i <a,g>_i|. The previous three runs tested PER-ITEM derivatives and
failed on items whose <a,g> is near zero -- a relative error with a vanishing denominator, which is the
sign cancellation this round exists to measure rather than a defect in the gradient. So the finite
difference is now taken on the same mean P takes.

AMENDMENT_1's two conditions carry over unchanged in form and in their numbers:
  1. min over alpha of |FD(alpha) - target| / |target| <= 1%
  2. halving ratios in [1.6, 2.4] for consecutive pairs from alpha=1 down to the pair before the argmin

Every prompt from this task is the same length -- a fixed template -- so items batch with no padding.

⚠ THE BACKWARD PASS MUST NOT BE BATCHED. The first version batched all 120 items through one
forward+backward and was OOM-killed at anon-rss 57.8 GB on a 59 GB box (confirmed from dmesg:
`global_oom, task=python3, total-vm 75121032kB`), because autograd retains every intermediate for
120 x 121 tokens x 28 layers in float64. So gradients are taken ONE ITEM AT A TIME -- 120 backward passes,
which is the cheap half -- while the alpha sweep, which needs no graph at all, batches under no_grad in
chunks of CHUNK. Batching where it is free, not where it is fatal.
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'R10_exhaustive'))

ALPHAS = (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125)
CHUNK = 20                       # forward-only batch size; see the OOM note below
CTRL1_REL = 0.01
LO, HI = 1.6, 2.4
N_ITEMS = 120


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import run as R10                                                    # noqa: N813
    from task import PERSONS, ROOMS

    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    args = ap.parse_args()
    rooms = list(ROOMS)

    tok = AutoTokenizer.from_pretrained(str(REPO / args.model), trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        str(REPO / args.model), trust_remote_code=True, dtype=torch.float64,
        attn_implementation='eager', device_map='cpu').eval()
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

    T, SCALE = {}, {}

    def mk(L, mod):
        def pre(_mod, inp):
            t = inp[0]
            if SCALE:
                t = t.clone()
                for (LL, h), f in SCALE.items():
                    if LL == L:
                        t[:, -1, h * HD:(h + 1) * HD] *= f
                return (t,) + inp[1:]
            if t.requires_grad:
                T[L] = t
            return None
        return mod.register_forward_pre_hook(pre)

    hooks = [mk(L, m.model.layers[L].self_attn.o_proj) for L in range(NL)]

    # ---- gather the same items the scans use, then batch them ----
    texts, cors = [], []
    with torch.no_grad():
        for s in R10.SEEDS:
            b = R10.bindings(s, rooms)
            q = next((p for p in single if p in b), None)
            if q is None:
                continue
            txt = R10.prompt(q, b)
            enc = tok(txt, return_tensors='pt')
            SCALE.clear()
            lg = m(**enc, use_cache=False).logits[0, -1]
            cor = b[q][1]
            if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
                continue
            texts.append(txt)
            cors.append(cor)
            if len(texts) >= N_ITEMS:
                break
    enc_all = tok(texts, return_tensors='pt')
    print(f'  {len(texts)} items, shape {tuple(enc_all["input_ids"].shape)}   float64 CPU   '
          f'chunk {CHUNK}', flush=True)
    if len(set(int(x.sum()) for x in enc_all['attention_mask'])) != 1:
        print('  -> STOP: prompts are not equal length; the batch would need padding and the last '
              'position would not be the query position for every row.')
        return 3

    cor_ix = torch.tensor([rid[c] for c in cors])
    oth_ix = torch.tensor([[rid[r] for r in rooms if r != c] for c in cors])

    def margins(lo, hi):
        e = {k: v[lo:hi] for k, v in enc_all.items()}
        lg = m(**e, use_cache=False).logits[:, -1]
        c = lg.gather(1, cor_ix[lo:hi, None]).squeeze(1)
        o = lg.gather(1, oth_ix[lo:hi]).max(1).values
        return c - o

    # ---- gradients ONE ITEM AT A TIME: the backward is what blows up, not the forward ----
    dots = {(L, h): [] for L in range(NL) for h in range(NH)}
    base = []
    for i in range(len(texts)):
        SCALE.clear(); T.clear()
        mg = margins(i, i + 1)
        base.append(float(mg))
        order = sorted(T)
        gs = torch.autograd.grad(mg.sum(), [T[L] for L in order])
        for L, gt in zip(order, gs):
            av = T[L][0, -1].detach().view(NH, HD)
            gv = gt[0, -1].detach().view(NH, HD)
            d = (av * gv).sum(1)
            for h in range(NH):
                dots[(L, h)].append(float(d[h]))
        if (i + 1) % 30 == 0:
            print(f'    gradients {i + 1}/{len(texts)}', flush=True)
    base = torch.tensor(base, dtype=torch.float64)
    print('  gradients done; every cell from one backward per item', flush=True)

    picks = [(L, h) for L in (NL // 3, 2 * NL // 3) for h in range(4)]
    per, ok = {}, True
    with torch.no_grad():
        for (L, h) in picks:
            target = sum(dots[(L, h)]) / len(dots[(L, h)])
            seq, rel = [], []
            for al in ALPHAS:
                SCALE.clear(); SCALE[(L, h)] = 1.0 - al
                acc = []
                for lo in range(0, len(texts), CHUNK):
                    hi = min(lo + CHUNK, len(texts))
                    acc.append(((base[lo:hi] - margins(lo, hi)) / al))
                fd = float(torch.cat(acc).mean())
                seq.append(fd)
                rel.append(abs(fd - target) / max(abs(target), 1e-300))
            SCALE.clear()
            jm = min(range(len(rel)), key=lambda j: rel[j])
            ratios = [rel[j] / rel[j + 1] for j in range(jm) if rel[j + 1] > 0]
            band = all(LO <= r <= HI for r in ratios) if ratios else False
            good = rel[jm] <= CTRL1_REL and band
            ok = ok and good
            per[f'L{L:02d}H{h:02d}'] = {
                'target_mean_dot': target, 'fd_seq': seq, 'rel_err_seq': rel,
                'rel_err_min': rel[jm], 'argmin_alpha': ALPHAS[jm],
                'halving_ratios_before_argmin': ratios, 'ratios_in_band': band, 'pass': good}
            print(f'    L{L:02d}H{h:02d}  target {target:+.6e}  min rel err {rel[jm]:.3e} '
                  f'@alpha {ALPHAS[jm]}  ratios '
                  f'{" ".join(f"{r:.2f}" for r in ratios)}  -> {"PASS" if good else "FAIL"}',
                  flush=True)
    for hk in hooks:
        hk.remove()

    out = {'model': args.tag, 'dtype': 'float64', 'device': 'cpu', 'n_items': len(texts),
           'alphas': list(ALPHAS), 'estimand': 'item MEAN, matching P = log|mean_i <a,g>_i|',
           'rule': 'AMENDMENT_1 conditions on the AMENDMENT_2 estimand',
           'per_cell': per, 'pass': ok}
    print(f'\n  CONTROL 1 on the estimand: {"PASS" if ok else "FAIL"}', flush=True)
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / f'r28_gate1_mean_{args.tag}.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0 if ok else 3


if __name__ == '__main__':
    sys.exit(main())
