#!/usr/bin/env python3
"""kappa = log|I| - log|<a_h, d margin / d a_h>|, in nats. Registered in PREREGISTRATION.md.

The gradient is taken on the o_proj INPUT slice -- exactly the tensor R10's ablation hook zeroes -- so
the predictor lives where the intervention acts. One backward pass per item covers every cell at once.

Both means are SIGNED means over the same items, so the predictor cancels across items exactly as the
target does. That makes Var(log|I|) = Var(P) + Var(kappa) + 2Cov(P, kappa) an identity BY CONSTRUCTION,
which is the property R26's budget lacked: its shares never referenced the pairing at all.

CONTROL 1 IS DEFINITIONAL AND HARD-RETURNS. If the gradient were hooked one module later, the
finite-difference limit would miss by exactly W_O and every kappa would be wrong by the same factor.
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
CTRL1_REL = 0.01                 # now on the MINIMUM over alpha, per AMENDMENT_1
CTRL1_RATIO_LO = 1.6             # two-sided band on the halving ratio in the truncation regime
CTRL1_RATIO_HI = 2.4
CTRL2_RHO = 0.90
CURV_ALPHA = 0.5
N_CURV_PER_SEXTILE = 4
SEED = 20260729
TARGETS = {'qwen2.5-1.5b': ('artifacts/model_qwen2.5-1.5b-instruct',
                            'R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json',
                            'R18_all_positions/results/r18_allpos_qwen2.5-1.5b.json'),
           'qwen2.5-3b': ('artifacts/model_qwen2.5-3b-instruct',
                          'R10_exhaustive/results/r10_exhaustive_qwen2.5-3b.json',
                          'R18_all_positions/results/r18_allpos_qwen2.5-3b.json')}


def spearman(a, b):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    x, y = rk(a), rk(b)
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = math.sqrt(sum((x[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((y[i] - my) ** 2 for i in range(n)))
    return num / (dx * dy) if dx > 0 and dy > 0 else float('nan')


def var(v):
    v = [x for x in v if x == x]
    if len(v) < 2:
        return float('nan')
    m = sum(v) / len(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def cov(a, b):
    p = [(x, y) for x, y in zip(a, b) if x == x and y == y]
    if len(p) < 2:
        return float('nan')
    ma = sum(x for x, _ in p) / len(p)
    mb = sum(y for _, y in p) / len(p)
    return sum((x - ma) * (y - mb) for x, y in p) / (len(p) - 1)


def r2(y, preds):
    n = len(y)
    X = [[1.0] + [p[i] for p in preds] for i in range(n)]
    k = len(X[0])
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    c = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    for i in range(k):
        p = max(range(i, k), key=lambda r: abs(A[r][i]))
        if abs(A[p][i]) < 1e-12:
            return float('nan')
        A[i], A[p] = A[p], A[i]
        c[i], c[p] = c[p], c[i]
        for r in range(i + 1, k):
            f = A[r][i] / A[i][i]
            for j in range(i, k):
                A[r][j] -= f * A[i][j]
            c[r] -= f * c[i]
    beta = [0.0] * k
    for i in range(k - 1, -1, -1):
        beta[i] = (c[i] - sum(A[i][j] * beta[j] for j in range(i + 1, k))) / A[i][i]
    my = sum(y) / n
    sst = sum((v - my) ** 2 for v in y)
    if sst <= 0:
        return float('nan')
    ssr = sum((y[i] - sum(beta[a] * X[i][a] for a in range(k))) ** 2 for i in range(n))
    return 1.0 - ssr / sst


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import run as R10                                                    # noqa: N813
    from task import PERSONS, ROOMS

    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    args = ap.parse_args()
    md, rf, ra = TARGETS[args.tag]
    ref = json.load(open(REPO / rf))
    rooms = ref['rooms'] if ref.get('rooms') else list(ROOMS)
    n_items = ref['n_items']

    tok = AutoTokenizer.from_pretrained(str(REPO / md), trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        str(REPO / md), trust_remote_code=True, dtype=torch.float32,
        attn_implementation='eager',
        device_map='cuda' if torch.cuda.is_available() else 'cpu').eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH

    def content_ids(s):
        return tok.encode(' ' + s, add_special_tokens=False)
    room_ids = {r: content_ids(r) for r in rooms}
    firsts = {ids[0] for ids in room_ids.values()}
    plen = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[plen] for r, ids in room_ids.items()}
    single = [p for p in PERSONS if len(content_ids(p)) == 1 + plen]

    T = {}                           # live o_proj-input tensors, for autograd.grad
    SCALE = {}                       # (L, h) -> factor applied to that head's slice, final position

    def mk(L, mod):
        def pre(_mod, inp):
            t = inp[0]
            if SCALE:
                t = t.clone()
                for (LL, h), f in SCALE.items():
                    if LL == L:
                        t[..., -1, h * HD:(h + 1) * HD] *= f
                return (t,) + inp[1:]
            # `autograd.grad` on the captured non-leaf tensors, NOT `.backward()`: backward would
            # allocate a .grad for every parameter -- 6 GB for 1.5b in float32, on a 16 GB card that
            # already holds the model. And a tensor hook cannot be registered under no_grad, which is
            # why capture is conditional on grad actually being enabled.
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
            enc = {k: v.to(m.device) for k, v in
                   tok(R10.prompt(q, b), return_tensors='pt').items()}
            cor = b[q][1]
            SCALE.clear()
            lg = m(**enc, use_cache=False).logits[0, -1]
            if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
                continue
            items.append((enc, cor, float(lg[rid[cor]]
                                          - max(lg[rid[r]] for r in rooms if r != cor))))
            if len(items) >= n_items:
                break
    print(f'  items {len(items)}   layers {NL}   heads {NH}', flush=True)

    # ---------- the forward+backward sweep: <a, g> per cell per item ----------
    dots = {(L, h): [] for L in range(NL) for h in range(NH)}
    norms = {(L, h): [] for L in range(NL) for h in range(NH)}
    for enc, cor, _bm in items:
        SCALE.clear()
        T.clear()
        mg = margin_of(enc, cor)
        order = sorted(T)
        gs = torch.autograd.grad(mg, [T[L] for L in order])
        for L, gt in zip(order, gs):
            av = T[L][0, -1].detach().view(NH, HD)
            gv = gt[0, -1].detach().view(NH, HD)
            d = (av * gv).sum(1)
            for h in range(NH):
                dots[(L, h)].append(float(d[h]))
                norms[(L, h)].append(float(av[h].norm()))

    # ---------- CONTROL 1: the finite-difference limit ----------
    # AMENDMENT_1: the rule is NOT read at the endpoint. Truncation error falls as alpha, roundoff
    # rises as 1/alpha, so the smallest alpha is the worst place to look and the original threshold
    # was below the float32 floor. Now: min over alpha of rel err <= 1%, AND the halving ratio must
    # lie in a TWO-SIDED band in the truncation-dominated regime (before each cell's own argmin).
    print(f'\n  CONTROL 1  need min-over-alpha rel err <= {CTRL1_REL} AND halving ratios in '
          f'[{CTRL1_RATIO_LO}, {CTRL1_RATIO_HI}] before the argmin', flush=True)
    c1 = {}
    ok1 = True
    picks = [(L, h) for L in (NL // 3, 2 * NL // 3) for h in range(4)]
    with torch.no_grad():
        for (L, h) in picks:
            errs = []
            for it in range(4):
                enc, cor, bm = items[it]
                want = dots[(L, h)][it]
                seq = []
                for al in ALPHAS:
                    SCALE.clear()
                    SCALE[(L, h)] = 1.0 - al
                    got = float(margin_of(enc, cor))
                    seq.append((bm - got) / al)
                SCALE.clear()
                rel_seq = [abs(v - want) / max(abs(want), 1e-12) for v in seq]
                jmin = min(range(len(rel_seq)), key=lambda j: rel_seq[j])
                ratios = [rel_seq[j] / rel_seq[j + 1] for j in range(jmin)
                          if rel_seq[j + 1] > 0]
                in_band = all(CTRL1_RATIO_LO <= r <= CTRL1_RATIO_HI for r in ratios) if ratios \
                    else False
                errs.append({'item': it, 'want': want, 'seq': seq, 'rel_err_seq': rel_seq,
                             'rel_err_min': rel_seq[jmin], 'argmin_alpha': ALPHAS[jmin],
                             'rel_err_smallest_alpha': rel_seq[-1],
                             'halving_ratios_before_argmin': ratios, 'ratios_in_band': in_band})
            worst_min = max(e['rel_err_min'] for e in errs)
            allband = all(e['ratios_in_band'] for e in errs)
            good = worst_min <= CTRL1_REL and allband
            ok1 = ok1 and good
            c1[f'L{L:02d}H{h:02d}'] = {'worst_rel_err_min': worst_min, 'ratios_in_band': allband,
                                       'pass': good, 'detail': errs}
            print(f'    L{L:02d}H{h:02d}  worst min-rel-err {worst_min:.3e}  ratios in band '
                  f'{allband}  -> {"PASS" if good else "FAIL"}', flush=True)
    out = {'model': args.tag, 'n_items': len(items), 'n_layers': NL, 'n_heads': NH,
           'alphas': list(ALPHAS), 'control1': {'per_cell': c1, 'pass': ok1}}
    if not ok1:
        out['verdict'] = 'STOPPED_CONTROL1_FAILED'
        out['inferential'] = False
        print('\n  -> STOP. The finite-difference limit does not reach <a,g>: the gradient is not on '
              'the\n     tensor the ablation acts on. No kappa is read.', flush=True)
        (HERE / 'results').mkdir(parents=True, exist_ok=True)
        json.dump(out, open(HERE / 'results' / f'r28_kappa_{args.tag}.json', 'w'), indent=1)
        for hk in hooks:
            hk.remove()
        return 3

    # ---------- the curvature control, registered before the run ----------
    print(f'\n  CURVATURE CONTROL  alpha={CURV_ALPHA} on '
          f'{N_CURV_PER_SEXTILE} cells per layer-sextile', flush=True)
    curv = {}
    with torch.no_grad():
        sext = [range(NL * i // 6, max(NL * i // 6 + 1, NL * (i + 1) // 6)) for i in range(6)]
        cells_c = []
        for rg in sext:
            L = list(rg)[len(list(rg)) // 2]
            for h in range(N_CURV_PER_SEXTILE):
                cells_c.append((L, h))
        for (L, h) in cells_c:
            d1, dh = [], []
            for enc, cor, bm in items:
                SCALE.clear(); SCALE[(L, h)] = 0.0
                d1.append(bm - float(margin_of(enc, cor)))
                SCALE.clear(); SCALE[(L, h)] = 1.0 - CURV_ALPHA
                dh.append(bm - float(margin_of(enc, cor)))
            SCALE.clear()
            m1 = sum(d1) / len(d1)
            mh = sum(dh) / len(dh)
            curv[f'L{L:02d}H{h:02d}'] = {'delta_full': m1, 'delta_half': mh,
                                         'quadratic_term': m1 - 2 * mh}
    out['curvature_control'] = {'alpha': CURV_ALPHA, 'cells': curv}
    print(f'    {len(curv)} cells measured; quadratic term = delta(1) - 2*delta(1/2)', flush=True)

    for hk in hooks:
        hk.remove()
    del m
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # ---------- kappa, per support ----------
    per = {}
    for support, path in (('I_final', rf), ('I_all', ra)):
        d = json.load(open(REPO / path))
        L2 = {int(k): v for k, v in d['layers'].items()}
        rows = []
        for lay in sorted(L2):
            ph = L2[lay]['per_head']
            for h in range(len(ph)):
                e = abs(ph[str(h)])
                dd = dots[(lay, h)]
                sm = sum(dd) / len(dd)
                am = sum(abs(x) for x in dd) / len(dd)
                if e <= 0 or sm == 0 or am <= 0:
                    continue
                P = math.log(abs(sm))
                rows.append({'layer': lay, 'head': h, 'logI': math.log(e), 'P': P,
                             'kappa': math.log(e) - P,
                             'C': math.log(am) - math.log(abs(sm)),
                             'size': math.log(sum(norms[(lay, h)]) / len(norms[(lay, h)]))})
        vt = var([r['logI'] for r in rows])
        vp = var([r['P'] for r in rows])
        vk = var([r['kappa'] for r in rows])
        ck = cov([r['P'] for r in rows], [r['kappa'] for r in rows])
        r2s, rk = [], []
        for lay in sorted(L2):
            g = [r for r in rows if r['layer'] == lay]
            if len(g) < 5:
                continue
            r2s.append(r2([r['logI'] for r in g], [[r['P'] for r in g]]))
            rk.append(spearman([r['kappa'] for r in g], [r['size'] for r in g]))

        def mean(v):
            v = [x for x in v if x == x]
            return sum(v) / len(v) if v else float('nan')
        deep = max(sorted(L2))
        per[support] = {
            'n_cells': len(rows),
            'var_logI_nats2': vt, 'var_P_nats2': vp, 'var_kappa_nats2': vk,
            'cov_2x_nats2': 2 * ck,
            'identity_sum': (vp + vk + 2 * ck) / vt,
            'share_P': vp / vt, 'share_kappa': vk / vt, 'share_cov': 2 * ck / vt,
            'sd_kappa_nats': math.sqrt(vk), 'sd_logI_nats': math.sqrt(vt),
            'mean_within_layer_r2_P': mean(r2s),
            'rho_bar_kappa_size': mean(rk),
            'var_C_over_var_logI': var([r['C'] for r in rows]) / vt,
            'mean_C_nats': mean([r['C'] for r in rows]),
            'deepest_layer': deep,
            'rows_deepest': [{'head': r['head'], 'P': r['P'], 'logI': r['logI']}
                             for r in rows if r['layer'] == deep]}
        p = per[support]
        print(f'\n  {support}  n {p["n_cells"]}   identity sum {p["identity_sum"]:.6f}  '
              f'(must be 1 exactly)', flush=True)
        print(f'    shares  P {p["share_P"]:+.4f}   kappa {p["share_kappa"]:+.4f}   '
              f'2cov {p["share_cov"]:+.4f}', flush=True)
        print(f'    R2bar(log|I| ~ P) {p["mean_within_layer_r2_P"]:.4f}   '
              f'sd(kappa) {p["sd_kappa_nats"]:.4f} nats   '
              f'rho_bar(kappa,size) {p["rho_bar_kappa_size"]:+.4f}   '
              f'Var(C)/Var {p["var_C_over_var_logI"]:.4f}   mean C {p["mean_C_nats"]:.4f} nats',
              flush=True)
    out['supports'] = per

    # ---------- CONTROL 2: the two pullbacks must agree at the deepest layer ----------
    dec = HERE.parent / 'R26_decomposition' / 'results' / 'r26_decompose.json'
    c2 = None
    if dec.exists():
        dd = json.load(open(dec))
        rec = dd['models'].get(args.tag)
        if rec:
            ph = rec['per_head']
            deep = per['I_final']['deepest_layer']
            a_ = [], []
            xs = [ph['size'][deep][h] + ph['align'][deep][h] for h in range(NH)]
            ys = [(math.log(abs(sum(dots[(deep, h)]) / len(dots[(deep, h)])))
                   if sum(dots[(deep, h)]) != 0 else float('nan')) for h in range(NH)]
            keep = [i for i in range(NH) if xs[i] == xs[i] and ys[i] == ys[i]]
            rho = spearman([xs[i] for i in keep], [ys[i] for i in keep])
            c2 = {'deepest_layer': deep, 'rho_P_vs_R26_size_plus_align': rho,
                  'n': len(keep), 'pass': rho >= CTRL2_RHO}
            print(f'\n  CONTROL 2  L{deep}: rho(P, R26 size+align) = {rho:+.4f} over n={len(keep)}'
                  f'  -> {"PASS" if rho >= CTRL2_RHO else "FAIL"} (need >= {CTRL2_RHO})', flush=True)
            del a_
    out['control2'] = c2
    out['inferential'] = bool(ok1 and c2 and c2['pass'])
    if not out['inferential']:
        print('\n  ** inferential = False. A registered control did not pass; every number above is '
              'DESCRIPTIVE\n     and the prediction matrix is NOT read. **', flush=True)
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / f'r28_kappa_{args.tag}.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
