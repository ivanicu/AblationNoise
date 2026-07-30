#!/usr/bin/env python3
"""Keep the 120-vector. Registered in R29_cancellation/PREREGISTRATION.md.

R10 and R18 computed Delta_{c,i} for every (cell, item) -- 218,880 numbers for 1.5b alone -- and stored only
the mean. This keeps the vector and emits the two coordinates the mean conflates:

    G_c      = log rms_i(Delta)                      nats
    Lambda_c = G_c - log|mean_i Delta|   >= 0        nats

plus, per cell, a jackknife-over-items precision for Lambda (so a threshold can be checked against the
instrument's own floor rather than assumed above it), max_i|Delta|/rms, and the fraction of items whose sign
matches the mean's. Per layer: the eigen-spectrum of the 120 x NH matrix of unit-normalised item patterns,
raw and after projecting out the layer-mean pattern, against two nulls simulated in this same process.

THE 8.8 GB TRAP IS AVOIDED RATHER THAN MANAGED. Materialising logits for 120 items x 121 positions x 151936
vocab is 8.8 GB. Only the final position is ever read, so the body runs `m.model(...)` and applies `lm_head`
to that one position -- the big tensor is never allocated at all.

NOTHING IS READ PAST THE POSITIVE CONTROL. It must reproduce R10's and R18's published per_head means, and
R11's per_head_sem, cell by cell on the same seeds.
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

CHUNK = 40
TOL_MEAN = 1e-5
TOL_SEM_REL = 1e-3
SEED = 20260729
N_NULL = 400


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import run as R10                                                    # noqa: N813
    from task import PERSONS, ROOMS

    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    ap.add_argument('--support', default='I_final', choices=['I_final', 'I_all'])
    ap.add_argument('--seed-offset', type=int, default=0)
    ap.add_argument('--ref', default='R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json')
    args = ap.parse_args()

    ref = json.load(open(REPO / args.ref))
    rooms = ref['rooms'] if ref.get('rooms') else list(ROOMS)
    n_items, want_bm = ref['n_items'], ref['base_margin']

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

    ACT = {}                        # L -> set of heads to zero

    def mk(L, mod):
        def pre(_mod, inp):
            hs = inp[0]
            if L in ACT and ACT[L]:
                hs = hs.clone()
                for h in ACT[L]:
                    if args.support == 'I_final':
                        hs[:, -1, h * HD:(h + 1) * HD] = 0
                    else:
                        hs[:, :, h * HD:(h + 1) * HD] = 0
                return (hs,) + inp[1:]
            return None
        return mod.register_forward_pre_hook(pre)

    hooks = [mk(L, m.model.layers[L].self_attn.o_proj) for L in range(NL)]

    texts, cors = [], []
    seeds = [x + args.seed_offset for x in R10.SEEDS]

    def margins(enc):
        """Only the FINAL position is ever read, so lm_head is applied to that alone -- the
        120 x 121 x 151936 logits tensor (8.8 GB) is never allocated."""
        hs = m.model(**enc).last_hidden_state[:, -1]
        return m.lm_head(hs)

    with torch.no_grad():
        for s in seeds:
            b = R10.bindings(s, rooms)
            q = next((p for p in single if p in b), None)
            if q is None:
                continue
            enc = {k: v.to(m.device) for k, v in
                   tok(R10.prompt(q, b), return_tensors='pt').items()}
            ACT.clear()
            lg = margins(enc)[0]
            cor = b[q][1]
            if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
                continue
            texts.append(R10.prompt(q, b))
            cors.append(cor)
            if len(texts) >= n_items:
                break
    enc_all = {k: v.to(m.device) for k, v in tok(texts, return_tensors='pt').items()}
    n = len(texts)
    print(f'  {args.tag} {args.support} offset {args.seed_offset}: {n} items, '
          f'shape {tuple(enc_all["input_ids"].shape)}, chunk {CHUNK}', flush=True)

    cor_ix = torch.tensor([rid[c] for c in cors], device=m.device)
    oth_ix = torch.tensor([[rid[r] for r in rooms if r != c] for c in cors], device=m.device)

    def margin_vec():
        out = []
        for lo in range(0, n, CHUNK):
            hi = min(lo + CHUNK, n)
            e = {k: v[lo:hi] for k, v in enc_all.items()}
            lg = margins(e)
            c = lg.gather(1, cor_ix[lo:hi, None]).squeeze(1)
            o = lg.gather(1, oth_ix[lo:hi]).max(1).values
            out.append((c - o).float())
        return torch.cat(out)

    with torch.no_grad():
        ACT.clear()
        base = margin_vec()
        bm = float(base.mean())
        print(f'  base_margin replayed {bm!r}   frozen {want_bm!r}   '
              f'|delta| {abs(bm - want_bm):.3e}', flush=True)

        cells = {}
        for L in range(NL):
            for h in range(NH):
                ACT.clear(); ACT[L] = {h}
                d = (base - margin_vec())
                cells[(L, h)] = d.cpu()
            if (L + 1) % 7 == 0:
                print(f'    layers {L + 1}/{NL}', flush=True)
        ACT.clear()
    for hk in hooks:
        hk.remove()

    # ---------- POSITIVE CONTROL: reproduce the published per-head numbers ----------
    # THE FAILING PATH MUST BE LEGIBLE. The first run printed only the worst-case numbers, so a
    # FAIL said "somewhere among 336 cells" and nothing else. Per-cell discrepancies are emitted
    # now, alongside each cell's own sd and SNR, because a sem is a difference of near-equal numbers
    # and a 5e-6 absolute perturbation per item is a large FRACTION of a near-dead cell's sd.
    worst_mean, worst_sem, nchk = 0.0, 0.0, 0
    diag = {}
    rL = {int(k): v for k, v in ref['layers'].items()}
    semref = None
    sp = (REPO / 'R11_instrument_noise' / 'results' / f'r11_itemsA_{args.tag}.json')
    if args.support == 'I_final' and args.seed_offset == 0 and sp.exists():
        semref = {int(k): v for k, v in json.load(open(sp))['layers'].items()}
    for (L, h), d in cells.items():
        if L not in rL:
            continue
        got = float(d.mean())
        dm = abs(got - rL[L]['per_head'][str(h)])
        worst_mean = max(worst_mean, dm)
        nchk += 1
        row = {'delta_mean': dm, 'mean': got, 'sd_items': float(d.std(unbiased=True))}
        if semref and L in semref and 'per_head_sem' in semref[L]:
            gs = float(d.std(unbiased=True)) / math.sqrt(n)
            ws = semref[L]['per_head_sem'][str(h)]
            if ws > 0:
                rel = abs(gs - ws) / ws
                worst_sem = max(worst_sem, rel)
                row.update({'rel_delta_sem': rel, 'sem_got': gs, 'sem_ref': ws,
                            'snr': abs(got) / gs if gs > 0 else float('inf')})
        diag[f'L{L:02d}H{h:02d}'] = row
    ok = (worst_mean <= TOL_MEAN and abs(bm - want_bm) <= TOL_MEAN
          and (semref is None or worst_sem <= TOL_SEM_REL))
    print(f'\n  POSITIVE CONTROL over {nchk} cells: worst |delta mean| {worst_mean:.3e} '
          f'(tol {TOL_MEAN})', flush=True)
    if semref:
        print(f'    worst relative |delta sem| {worst_sem:.3e} (tol {TOL_SEM_REL})', flush=True)
    print(f'    -> {"PASS" if ok else "FAIL"}', flush=True)

    out = {'model': args.tag, 'support': args.support, 'seed_offset': args.seed_offset,
           'n_items': n, 'n_layers': NL, 'n_heads': NH, 'chunk': CHUNK,
           'base_margin_replayed': bm, 'base_margin_frozen': want_bm,
           'control_per_cell': diag,
           'control': {'n_cells_checked': nchk, 'worst_abs_delta_mean': worst_mean,
                       'worst_rel_delta_sem': worst_sem if semref else None,
                       'tol_mean': TOL_MEAN, 'tol_sem_rel': TOL_SEM_REL, 'pass': ok}}
    rs = sorted(((v['rel_delta_sem'], k) for k, v in diag.items() if 'rel_delta_sem' in v),
                reverse=True)
    if rs:
        import statistics as _st
        out['control']['rel_delta_sem_median'] = _st.median([r for r, _ in rs])
        out['control']['rel_delta_sem_p95'] = rs[max(0, int(0.05 * len(rs)) - 1)][0]
        out['control']['n_cells_over_tol'] = sum(1 for r, _ in rs if r > TOL_SEM_REL)
        print(f'    per-cell relative sem discrepancy: median '
              f'{out["control"]["rel_delta_sem_median"]:.3e}   p95 '
              f'{out["control"]["rel_delta_sem_p95"]:.3e}   over tol '
              f'{out["control"]["n_cells_over_tol"]} of {len(rs)}', flush=True)
        for r, k in rs[:5]:
            v = diag[k]
            print(f'      {k}  rel {r:.3e}  sd_items {v["sd_items"]:.3e}  '
                  f'snr {v.get("snr", float("nan")):.2f}', flush=True)
    if not ok:
        out['inferential'] = False
        print('\n  -> STOP. The per-item pipeline does not reproduce the published per-head numbers. '
              'No Lambda is read.', flush=True)
        (HERE / 'results').mkdir(parents=True, exist_ok=True)
        json.dump(out, open(HERE / 'results' /
                            f'r29_scan_{args.tag}_{args.support}_off{args.seed_offset}.json',
                            'w'), indent=1)
        return 3

    # ---------- the coordinates ----------
    import statistics as st
    per = {}
    for (L, h), d in cells.items():
        v = d.tolist()
        mu = sum(v) / n
        sd = math.sqrt(sum((x - mu) ** 2 for x in v) / (n - 1))
        rms = math.sqrt(sum(x * x for x in v) / n)
        if rms <= 0 or mu == 0:
            continue
        G = math.log(rms)
        Lam = G - math.log(abs(mu))
        # jackknife-over-items precision for Lambda: the instrument's own floor, per cell
        jk = []
        s1, s2 = sum(v), sum(x * x for x in v)
        for x in v:
            m1 = (s1 - x) / (n - 1)
            r2_ = (s2 - x * x) / (n - 1)
            if r2_ <= 0 or m1 == 0:
                continue
            jk.append(0.5 * math.log(r2_) - math.log(abs(m1)))
        jse = (math.sqrt((len(jk) - 1) / len(jk) * sum((x - sum(jk) / len(jk)) ** 2 for x in jk))
               if len(jk) > 2 else float('nan'))
        half = n // 2
        def lam(sub):
            mm = sum(sub) / len(sub)
            rr = math.sqrt(sum(x * x for x in sub) / len(sub))
            return (math.log(rr) - math.log(abs(mm))) if rr > 0 and mm != 0 else float('nan')
        per[f'L{L:02d}H{h:02d}'] = {
            'layer': L, 'head': h, 'mean': mu, 'sd_items': sd, 'rms': rms,
            'logI': math.log(abs(mu)), 'G': G, 'Lambda': Lam,
            'lambda_jackknife_se_nats': jse,
            'lambda_half1': lam(v[:half]), 'lambda_half2': lam(v[half:]),
            'logI_half1': math.log(abs(sum(v[:half]) / half)) if sum(v[:half]) != 0 else float('nan'),
            'logI_half2': math.log(abs(sum(v[half:]) / (n - half))) if sum(v[half:]) != 0
            else float('nan'),
            'max_over_rms': max(abs(x) for x in v) / rms,
            'sign_frac': sum(1 for x in v if (x > 0) == (mu > 0)) / n,
            'snr': abs(mu) / (sd / math.sqrt(n)) if sd > 0 else float('inf')}
    out['per_cell'] = per
    jse_med = st.median([v['lambda_jackknife_se_nats'] for v in per.values()
                         if v['lambda_jackknife_se_nats'] == v['lambda_jackknife_se_nats']])
    out['median_lambda_jackknife_se_nats'] = jse_med
    print(f'\n  cells {len(per)}   median jackknife SE of Lambda {jse_med:.4f} nats '
          f'(the instrument floor for the 0.15 gate)', flush=True)
    for nm in ('Lambda', 'G', 'max_over_rms', 'sign_frac'):
        xs = [v[nm] for v in per.values() if v[nm] == v[nm]]
        print(f'    {nm:<14} median {st.median(xs):.4f}   min {min(xs):.4f}   max {max(xs):.4f}',
              flush=True)

    # ---------- per-layer eigen-spectrum of the item-pattern matrix ----------
    import random
    rng = random.Random(SEED)
    eig = {}
    for L in range(NL):
        cols = []
        for h in range(NH):
            v = cells[(L, h)].tolist()
            nrm = math.sqrt(sum(x * x for x in v))
            if nrm > 0:
                cols.append([x / nrm for x in v])
        if len(cols) < 2:
            continue

        def spec(cs):
            k = len(cs)
            gram = [[sum(cs[a][i] * cs[b][i] for i in range(n)) for b in range(k)]
                    for a in range(k)]
            ev = sym_eig(gram)
            tot = sum(ev)
            return (max(ev) / tot) if tot > 0 else float('nan')
        raw = spec(cols)
        mean_pat = [sum(c[i] for c in cols) / len(cols) for i in range(n)]
        mn = math.sqrt(sum(x * x for x in mean_pat))
        proj = []
        if mn > 0:
            u = [x / mn for x in mean_pat]
            for c in cols:
                d = sum(c[i] * u[i] for i in range(n))
                r = [c[i] - d * u[i] for i in range(n)]
                rn = math.sqrt(sum(x * x for x in r))
                if rn > 0:
                    proj.append([x / rn for x in r])
        resign = []
        for _ in range(20):
            cs = [[x * (1 if rng.random() < .5 else -1) for x in c] for c in cols]
            resign.append(spec(cs))
        iid = []
        for _ in range(20):
            cs = []
            for _h in range(len(cols)):
                z = [rng.gauss(0, 1) for _ in range(n)]
                zn = math.sqrt(sum(x * x for x in z))
                cs.append([x / zn for x in z])
            iid.append(spec(cs))
        eig[str(L)] = {'lambda1_share_raw': raw,
                       'lambda1_share_mean_projected': spec(proj) if len(proj) > 1 else None,
                       'null_resign_median': st.median(resign),
                       'null_iid_median': st.median(iid), 'n_cols': len(cols)}
    out['layer_eigen'] = eig
    rs = [v['lambda1_share_raw'] for v in eig.values()]
    print(f'\n  lambda1 share, per layer: median {st.median(rs):.4f}   '
          f'iid null median {st.median([v["null_iid_median"] for v in eig.values()]):.4f}   '
          f'resign null median {st.median([v["null_resign_median"] for v in eig.values()]):.4f}',
          flush=True)

    out['inferential'] = True
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / f'r29_scan_{args.tag}_{args.support}_off{args.seed_offset}.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


def sym_eig(a, iters=200):
    """Jacobi eigenvalues of a small symmetric matrix. No numpy dependency in this path."""
    k = len(a)
    A = [row[:] for row in a]
    for _ in range(iters):
        off, p, q = 0.0, 0, 1
        for i in range(k):
            for j in range(i + 1, k):
                if abs(A[i][j]) > off:
                    off, p, q = abs(A[i][j]), i, j
        if off < 1e-12:
            break
        app, aqq, apq = A[p][p], A[q][q], A[p][q]
        th = 0.5 * math.atan2(2 * apq, aqq - app)
        c, s = math.cos(th), math.sin(th)
        for i in range(k):
            aip, aiq = A[i][p], A[i][q]
            A[i][p] = c * aip - s * aiq
            A[i][q] = s * aip + c * aiq
        for i in range(k):
            api, aqi = A[p][i], A[q][i]
            A[p][i] = c * api - s * aqi
            A[q][i] = s * api + c * aqi
    return [A[i][i] for i in range(k)]


if __name__ == '__main__':
    sys.exit(main())
