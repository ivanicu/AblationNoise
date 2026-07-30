#!/usr/bin/env python3
"""R26 -- what GENERATES the per-head effect distribution. Registered in PREREGISTRATION.md.

sigma(log|I|) is 1.10 to 1.29 nats and is the same in both checkpoints under both supports to within
8%. Twenty-five rounds measured that width and none asked what produces it. Static weight size is
already dead as an explanation (3.4% of the variance, within-layer rho -0.023).

    size_lh  = log ||o_lh||                              o_lh = W_O[:, h*HD:(h+1)*HD] @ z_lh
    align_lh = log |<o_hat_lh, delta_u_hat_l>|
    Var(log|I|) = Var(size) + Var(align) + 2 Cov(size, align)        all nats^2

ONE forward pass per prompt. NO ABLATIONS -- the whole point is that if this explains the scan, a
40,000-forward-pass measurement was a 120-forward-pass measurement.

THE READOUT DIRECTION IS PULLED BACK THROUGH THE FINAL RMSNorm EXACTLY, not approximated by gamma*du.
For y = gamma * x / r with r = sqrt(mean(x^2) + eps),
    (J^T v)_j = (gamma*v)_j / r  -  x_j <gamma*v, x> / (n r^3)
so the direction a head must align with is that vector, not the raw unembedding difference. Using
gamma*du alone would leave the component along x uncancelled, and x is the residual stream itself --
i.e. it would build the confound this round exists to measure into the measurement.

Gates 1 and 2 (weight and behavioural identity) already passed. Gate 3 lives here: at the deepest
layer the first-order prediction size+align must rank-correlate with |I_final| at rho >= 0.70, or
world C wins and the shallow layers are never read. Gate 4, the sham direction, likewise.
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'R10_exhaustive'))

GATE3_RHO = 0.70
GATE4_BOUND = 0.114
SEED = 20260729


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
    n = len(v)
    if n < 2:
        return float('nan')
    m = sum(v) / n
    return sum((x - m) ** 2 for x in v) / (n - 1)


def cov(a, b):
    p = [(x, y) for x, y in zip(a, b) if x == x and y == y]
    if len(p) < 2:
        return float('nan')
    ma = sum(x for x, _ in p) / len(p)
    mb = sum(y for _, y in p) / len(p)
    return sum((x - ma) * (y - mb) for x, y in p) / (len(p) - 1)


def partial_spearman(a, b, controls):
    """Spearman of a and b after linearly removing each control from both, on ranks."""
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for i, ix in enumerate(o):
            r[ix] = float(i)
        return r

    def resid(y, xs):
        y = rk(y)
        xs = [rk(x) for x in xs]
        for x in xs:                              # sequential simple regressions; controls are few
            mx, my = sum(x) / len(x), sum(y) / len(y)
            sxx = sum((v - mx) ** 2 for v in x)
            if sxx <= 0:
                continue
            beta = sum((x[i] - mx) * (y[i] - my) for i in range(len(y))) / sxx
            y = [y[i] - beta * (x[i] - mx) for i in range(len(y))]
        return y
    return spearman(resid(a, controls), resid(b, controls))


def run_model(tag, model_dir, ref_final, ref_all, rng_seed=SEED):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import run as R10                                                    # noqa: N813
    from task import PERSONS, ROOMS

    ref = json.load(open(REPO / ref_final))
    rooms = ref['rooms'] if ref.get('rooms') else list(ROOMS)
    n_items = ref['n_items']

    tok = AutoTokenizer.from_pretrained(str(REPO / model_dir), trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        str(REPO / model_dir), trust_remote_code=True, dtype=torch.float32,
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

    # capture o_proj INPUT: the concatenated per-head attention output, at the query position
    Z = {}

    def mk(L, mod):
        def pre(_mod, a):
            Z[L] = a[0][0, -1].detach().float()
            return None
        return mod.register_forward_pre_hook(pre)

    hooks, WO = [], {}
    for L in range(NL):
        op = m.model.layers[L].self_attn.o_proj
        hooks.append(mk(L, op))
        WO[L] = op.weight.detach().float()                # (hidden_out, hidden_in)

    # the final residual stream, before the final norm
    X = {}

    def cap_x(_mod, a):
        X['x'] = a[0][0, -1].detach().float()
        return None
    hooks.append(m.model.norm.register_forward_pre_hook(cap_x))

    gamma = m.model.norm.weight.detach().float()
    eps = getattr(m.model.norm, 'variance_epsilon', None)
    if eps is None:
        eps = getattr(m.model.norm, 'eps', 1e-6)
    WU = m.lm_head.weight.detach().float()                # (vocab, hidden)
    n_hidden = gamma.numel()

    g = torch.Generator(device='cpu').manual_seed(rng_seed)
    sham_raw = torch.randn(n_hidden, generator=g).to(gamma.device)

    def pullback(du, x):
        """Exact first-order pullback of a logit-space direction through RMSNorm."""
        r = torch.sqrt((x * x).mean() + eps)
        gv = gamma * du
        return gv / r - x * torch.dot(gv, x) / (n_hidden * r ** 3)

    acc = {'size': [[[] for _ in range(NH)] for _ in range(NL)],
           'align': [[[] for _ in range(NH)] for _ in range(NL)],
           'align_signed': [[[] for _ in range(NH)] for _ in range(NL)],
           'align_sham': [[[] for _ in range(NH)] for _ in range(NL)]}
    n = 0
    with torch.no_grad():
        for s in R10.SEEDS:
            b = R10.bindings(s, rooms)
            q = next((p for p in single if p in b), None)
            if q is None:
                continue
            enc = {k: v.to(m.device) for k, v in
                   tok(R10.prompt(q, b), return_tensors='pt').items()}
            cor = b[q][1]
            lg = m(**enc, use_cache=False).logits[0, -1]
            if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
                continue
            other = max((r for r in rooms if r != cor), key=lambda r: lg[rid[r]].item())
            x = X['x']
            du = WU[rid[cor]] - WU[rid[other]]
            d = pullback(du, x)
            d = d / d.norm()
            dsh = pullback(sham_raw * (du.norm() / sham_raw.norm()), x)
            dsh = dsh / dsh.norm()
            for L in range(NL):
                z = Z[L]
                for h in range(NH):
                    o = WO[L][:, h * HD:(h + 1) * HD] @ z[h * HD:(h + 1) * HD]
                    nrm = o.norm()
                    acc['size'][L][h].append(float(nrm))
                    if nrm > 0:
                        c = float(torch.dot(o / nrm, d))
                        acc['align'][L][h].append(abs(c))
                        acc['align_signed'][L][h].append(c)
                        acc['align_sham'][L][h].append(abs(float(torch.dot(o / nrm, dsh))))
            n += 1
            if n >= n_items:
                break
    for hk in hooks:
        hk.remove()
    del m
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    def logmean(v):
        mu = sum(v) / len(v) if v else 0.0
        return math.log(mu) if mu > 0 else float('nan')

    per = {'n_items': n, 'n_layers': NL, 'n_heads': NH}
    for key in ('size', 'align', 'align_sham'):
        per[key] = [[logmean(acc[key][L][h]) for h in range(NH)] for L in range(NL)]
    per['align_signed_var'] = [[var(acc['align_signed'][L][h]) for h in range(NH)]
                               for L in range(NL)]
    return per


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    args = ap.parse_args()

    targets = {
        'qwen2.5-1.5b': ('artifacts/model_qwen2.5-1.5b-instruct',
                         'R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json',
                         'R18_all_positions/results/r18_allpos_qwen2.5-1.5b.json'),
        'qwen2.5-3b': ('artifacts/model_qwen2.5-3b-instruct',
                       'R10_exhaustive/results/r10_exhaustive_qwen2.5-3b.json',
                       'R18_all_positions/results/r18_allpos_qwen2.5-3b.json')}
    if args.only:
        targets = {k: v for k, v in targets.items() if k == args.only}

    out = {'seed': SEED, 'gate3_rho': GATE3_RHO, 'gate4_bound': GATE4_BOUND, 'models': {}}
    for tag, (md, rf, ra) in targets.items():
        print(f'\n  === {tag} ===', flush=True)
        per = run_model(tag, md, rf, ra)
        NL, NH = per['n_layers'], per['n_heads']
        print(f'    items {per["n_items"]}   layers {NL}   heads {NH}', flush=True)
        rec = {'per_head': per, 'supports': {}}

        for support, path in (('I_final', rf), ('I_all', ra)):
            d = json.load(open(REPO / path))
            L = {int(k): v for k, v in d['layers'].items()}
            rows = []
            for lay in sorted(L):
                ph = L[lay]['per_head']
                for h in range(len(ph)):
                    e = abs(ph[str(h)])
                    rows.append({'layer': lay, 'head': h,
                                 'logI': math.log(e) if e > 0 else float('nan'),
                                 'size': per['size'][lay][h],
                                 'align': per['align'][lay][h],
                                 'align_sham': per['align_sham'][lay][h]})
            good = [r for r in rows if all(r[k] == r[k] for k in ('logI', 'size', 'align'))]
            v_tot = var([r['logI'] for r in good])
            v_s = var([r['size'] for r in good])
            v_a = var([r['align'] for r in good])
            c_sa = cov([r['size'] for r in good], [r['align'] for r in good])
            budget = {
                'n_cells': len(good), 'var_logI_nats2': v_tot,
                'var_size_nats2': v_s, 'var_align_nats2': v_a, 'cov_2x_nats2': 2 * c_sa,
                'share_size': v_s / v_tot, 'share_align': v_a / v_tot,
                'share_cov': 2 * c_sa / v_tot,
                'sum_of_shares': (v_s + v_a + 2 * c_sa) / v_tot,
                # THE SHORTFALL IS THE MEASUREMENT, not a rounding remark. If log|I| were size+align
                # exactly, the three shares would sum to 1 BY CONSTRUCTION. They do not, and the gap
                # is how much of the effect's variance is not a first-order property of the head's own
                # write at all -- i.e. how much is propagation. A quantity with a unit, comparable
                # across every cell, which is the form this round was asked to deliver.
                'residual_share': 1.0 - (v_s + v_a + 2 * c_sa) / v_tot,
                'residual_nats2': v_tot - (v_s + v_a + 2 * c_sa),
                'sd_logI_nats': math.sqrt(v_tot), 'sd_size_nats': math.sqrt(v_s),
                'sd_align_nats': math.sqrt(v_a)}

            # within-layer rho, raw and partialled on (depth, layer mean logI)
            rb = {'size': [], 'align': [], 'sham': [], 'sum': [],
                  'size_partial': [], 'align_partial': []}
            for lay in sorted(L):
                g = [r for r in good if r['layer'] == lay]
                if len(g) < 4:
                    continue
                yi = [r['logI'] for r in g]
                rb['size'].append(spearman([r['size'] for r in g], yi))
                rb['align'].append(spearman([r['align'] for r in g], yi))
                rb['sham'].append(spearman([r['align_sham'] for r in g], yi))
                rb['sum'].append(spearman([r['size'] + r['align'] for r in g], yi))
            # depth and layer-mean cannot vary WITHIN a layer, so the partial is taken over ALL
            # cells at once -- stated because a within-layer partial on a constant is undefined
            dep = [r['layer'] for r in good]
            lm = {lay: (sum(r['logI'] for r in good if r['layer'] == lay)
                        / max(1, sum(1 for r in good if r['layer'] == lay)))
                  for lay in sorted(L)}
            mu = [lm[r['layer']] for r in good]
            allc = {
                'size_raw': spearman([r['size'] for r in good], [r['logI'] for r in good]),
                'align_raw': spearman([r['align'] for r in good], [r['logI'] for r in good]),
                'size_partial_depth_mu': partial_spearman(
                    [r['size'] for r in good], [r['logI'] for r in good], [dep, mu]),
                'align_partial_depth_mu': partial_spearman(
                    [r['align'] for r in good], [r['logI'] for r in good], [dep, mu])}

            def mean(v):
                v = [x for x in v if x == x]
                return sum(v) / len(v) if v else float('nan')
            bars = {f'rho_bar_{k}': mean(v) for k, v in rb.items() if v}
            deep = max(sorted(L))
            gd = [r for r in good if r['layer'] == deep]
            g3 = spearman([r['size'] + r['align'] for r in gd], [r['logI'] for r in gd])
            rec['supports'][support] = {
                'budget': budget, 'rho_bars': bars, 'pooled': allc,
                'gate3_deepest_layer': deep, 'gate3_rho_sum_vs_logI': g3,
                'gate3_pass': g3 >= GATE3_RHO,
                'gate4_rho_bar_sham': bars.get('rho_bar_sham'),
                'gate4_pass': abs(bars.get('rho_bar_sham', 9)) <= GATE4_BOUND,
                'per_layer_rho': rb}
            b = budget
            print(f'    {support}  n {b["n_cells"]:<5} sd(log|I|) {b["sd_logI_nats"]:.3f} nats   '
                  f'Var {b["var_logI_nats2"]:.4f} nats^2', flush=True)
            print(f'      shares  size {b["share_size"]:+.4f}   align {b["share_align"]:+.4f}   '
                  f'2cov {b["share_cov"]:+.4f}   sum {b["sum_of_shares"]:.4f}', flush=True)
            print(f'      RESIDUAL not explained by a first-order write: '
                  f'{b["residual_share"]:.4f} of the variance = {b["residual_nats2"]:.4f} nats^2',
                  flush=True)
            print(f'      rho_bar size {bars.get("rho_bar_size", float("nan")):+.4f}   '
                  f'align {bars.get("rho_bar_align", float("nan")):+.4f}   '
                  f'sham {bars.get("rho_bar_sham", float("nan")):+.4f}   '
                  f'sum {bars.get("rho_bar_sum", float("nan")):+.4f}', flush=True)
            print(f'      pooled partialled on (depth, layer mean): size '
                  f'{allc["size_partial_depth_mu"]:+.4f}  align '
                  f'{allc["align_partial_depth_mu"]:+.4f}', flush=True)
            print(f'      GATE 3 deepest L{deep}: rho(size+align, log|I|) = {g3:+.4f}  '
                  f'-> {"PASS" if g3 >= GATE3_RHO else "FAIL"} (need >= {GATE3_RHO})', flush=True)
            print(f'      GATE 4 sham rho_bar {bars.get("rho_bar_sham", float("nan")):+.4f}  '
                  f'-> {"PASS" if abs(bars.get("rho_bar_sham", 9)) <= GATE4_BOUND else "FAIL"}'
                  f' (need |.| <= {GATE4_BOUND})', flush=True)
        out['models'][tag] = rec

    # AMENDMENT_4 of R24 made this standing one round earlier and R26 did not carry it: a failed
    # control means the verdict is UNVERIFIED and the numbers are DESCRIPTIVE. Gate 3 failed in every
    # cell and nothing was flagged, so a reader of this JSON had no marker at all.
    #
    # And the budget's own shares are worse than unflagged -- they are PERMUTATION-INVARIANT, proven
    # in attack_budget.py at max|delta| ~ 1e-16 over 10000 draws with P(null >= obs) = 1.0000. A
    # statistic whose null is a point mass at the observed value cannot support any world. The
    # `residual_share` is additionally not a residual: Var(log|I| - (size+align))/Var(log|I|) comes to
    # 0.8418 / 1.6118 / 0.8358 / 1.6376, above 1 in two cells, so the budget was never an identity.
    gates = [sr for r in out['models'].values() for sr in r['supports'].values()]
    out['inferential'] = all(g['gate3_pass'] and g['gate4_pass'] for g in gates) if gates else False
    out['n_gate3_fail'] = sum(1 for g in gates if not g['gate3_pass'])
    out['n_gate4_fail'] = sum(1 for g in gates if not g['gate4_pass'])
    out['budget_shares_are_permutation_invariant'] = True
    out['budget_is_not_an_identity'] = True
    out['residual_share_is_void'] = True
    if not out['inferential']:
        print(f'\n  ** inferential = False. Gate 3 failed in {out["n_gate3_fail"]} of {len(gates)} '
              f'cells. **\n  Every share in this file is DESCRIPTIVE, and `residual_share` is VOID '
              f'-- see attack_budget.py.')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r26_decompose.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    print('  NO WORLD IS DECLARED HERE. The prediction matrix is read in a separate step, and only '
          'if\n  gates 3 and 4 pass in the cells being read.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
