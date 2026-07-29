#!/usr/bin/env python3
"""Q2 -- what STRUCTURES the within-layer heterogeneity? The first candidate that costs nothing.

Every round in this repository has treated a layer's heads as an exchangeable population and reported
one number for its spread. THE WEIGHTS SAY THEY ARE NOT EXCHANGEABLE. Qwen2.5 uses grouped-query
attention: 1.5b has 12 query heads over 2 KV heads, 3b has 16 over 2. Verified from the checkpoints'
own config.json, and the mapping from `transformers.models.qwen2.modeling_qwen2.repeat_kv`, which is
repeat_interleave semantics -- so query head h reads KV head h // n_rep. Heads 0..5 of every 1.5b
layer share one key/value stream; heads 6..11 share another.

So each layer arrives with a HARD PARTITION imposed by the architecture, free, needing no GPU and no
new forward pass. The quantity is the fraction of a layer's ablation-effect variance that the
partition explains -- eta squared, dimensionless, in [0,1], comparable across every layer, support
and model.

THIS FILE EMITS NUMBERS AND NO VERDICT. The decision threshold is not the author's to choose.

The null is WITHIN-LAYER PERMUTATION OF HEAD LABELS. Under exchangeability the group assignment is
arbitrary, so permuting it holds the layer's own distribution exactly fixed and randomises only the
partition. Nothing is pooled across layers, so this null cannot hit the mixture trap that killed
three of R23's.

The negative control is CALIBRATED, not run once: 200 draws, and the empirical rejection rate is
emitted as a number. A single-draw control is a coin flip -- that error was made twice in R24.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

SEED = 20260729
N_PERM = 20000
N_CAL = 200
ALPHA_REPORTED = 0.05               # for the calibration rate only; NOT a decision threshold

# from each checkpoint's own config.json, fetched 2026-07-29
GQA = {'qwen2.5-1.5b': {'n_heads': 12, 'n_kv': 2}, 'qwen2.5-3b': {'n_heads': 16, 'n_kv': 2}}


def eta_sq(v, g):
    """Fraction of variance explained by the partition. Dimensionless, in [0, 1]."""
    n = len(v)
    gm = sum(v) / n
    tot = sum((x - gm) ** 2 for x in v)
    if tot <= 0:
        return float('nan')
    btw = 0.0
    for lab in set(g):
        m = [v[i] for i in range(n) if g[i] == lab]
        btw += len(m) * (sum(m) / len(m) - gm) ** 2
    return btw / tot


def groups(n_heads, n_kv):
    rep = n_heads // n_kv
    return [h // rep for h in range(n_heads)]


def layer_test(v, g, rng, nperm=N_PERM):
    obs = eta_sq(v, g)
    if obs != obs:
        return None
    idx = list(range(len(v)))
    hits = 0
    for _ in range(nperm):
        rng.shuffle(idx)
        if eta_sq([v[i] for i in idx], g) >= obs:
            hits += 1
    return {'eta_sq': obs, 'p': (1 + hits) / (1 + nperm),
            'group_means': {str(lab): sum(v[i] for i in range(len(v)) if g[i] == lab)
                            / sum(1 for i in range(len(v)) if g[i] == lab)
                            for lab in sorted(set(g))}}


def combined(profile, g, rng, nperm=N_PERM):
    """Sum of eta squared across layers, against JOINT within-layer permutation.

    Independent layers, one null draw permutes every layer's labels at once. Far more powerful than
    reading 28 separate p-values, and it needs no multiplicity correction because it is ONE test."""
    obs = sum(e for e in (eta_sq(v, g) for v in profile) if e == e)
    idx = list(range(len(g)))
    null = []
    for _ in range(nperm):
        s = 0.0
        for v in profile:
            rng.shuffle(idx)
            e = eta_sq([v[i] for i in idx], g)
            if e == e:
                s += e
        null.append(s)
    null.sort()
    # eta squared is POSITIVELY BIASED: with k groups and n heads its null expectation is
    # (k-1)/(n-1), not zero -- 1/11 for 12 heads, 1/15 for 16. The permutation null already carries
    # that bias so the p-value is valid, but the raw value must never be quoted as "13% explained"
    # without it. The excess over the null is the reportable effect size.
    k = len(set(g))
    exp = (k - 1) / (len(g) - 1)
    return {'sum_eta_sq': obs, 'n_layers': len(profile),
            'null_expected_eta_sq': exp,
            'excess_eta_sq_over_null': obs / len(profile) - exp,
            'mean_eta_sq': obs / len(profile),
            'p': (1 + sum(1 for x in null if x >= obs)) / (1 + nperm),
            'null_median': null[len(null) // 2], 'null_p95': null[int(.95 * (len(null) - 1))]}


def load(model, support, absolute):
    f = (REPO / 'R10_exhaustive' / 'results' / f'r10_exhaustive_{model}.json' if support == 'I_final'
         else REPO / 'R18_all_positions' / 'results' / f'r18_allpos_{model}.json')
    if not f.exists():
        return None
    d = json.load(open(f))
    L = {int(k): v for k, v in d['layers'].items()}
    out = []
    for lay in sorted(L):
        ph = L[lay]['per_head']
        v = [ph[str(h)] for h in range(len(ph))]
        out.append([abs(x) for x in v] if absolute else v)
    return out


def synth_flat(rng, nlay, n_heads, scale):
    return [[rng.gauss(0, scale) for _ in range(n_heads)] for _ in range(nlay)]


def synth_grouped(rng, nlay, n_heads, n_kv, scale, delta):
    g = groups(n_heads, n_kv)
    return [[rng.gauss(0, scale) + delta * g[h] for h in range(n_heads)] for _ in range(nlay)]


def main():
    rng = random.Random(SEED)
    out = {'seed': SEED, 'n_perm': N_PERM, 'n_calibration_draws': N_CAL, 'gqa': GQA,
           'head_to_group_rule': 'h // (n_heads // n_kv), from repeat_kv repeat_interleave semantics',
           'alpha_used_for_calibration_only': ALPHA_REPORTED}

    # ---------- CALIBRATION, not a pass/fail: what is this test's actual size? ----------
    print(f'  CALIBRATION  {N_CAL} exchangeable draws per cell, empirical rejection rate at '
          f'{ALPHA_REPORTED}')
    cal = {}
    for model, cfg in GQA.items():
        g = groups(cfg['n_heads'], cfg['n_kv'])
        nlay = 28 if model == 'qwen2.5-1.5b' else 36
        rej = 0
        ps = []
        for _ in range(N_CAL):
            pr = synth_flat(rng, nlay, cfg['n_heads'], 1.0)
            p = combined(pr, g, rng, 400)['p']
            ps.append(p)
            rej += (p < ALPHA_REPORTED)
        ps.sort()
        cal[model] = {'rejection_rate': rej / N_CAL, 'p_median': ps[N_CAL // 2],
                      'p_min': ps[0], 'n_draws': N_CAL}
        print(f'    {model:<14} rejection {rej / N_CAL:.4f}   median p {ps[N_CAL // 2]:.4f}   '
              f'min p {ps[0]:.4f}')
    out['calibration_exchangeable'] = cal

    # ---------- POWER, so a null has a size: what delta does it take to fire? ----------
    print(f'\n  POWER  planted group offset, in units of the within-group sd')
    pw = {}
    for model, cfg in GQA.items():
        g = groups(cfg['n_heads'], cfg['n_kv'])
        nlay = 28 if model == 'qwen2.5-1.5b' else 36
        row = {}
        for delta in (0.10, 0.25, 0.50, 1.00):
            hit = 0
            for _ in range(40):
                pr = synth_grouped(rng, nlay, cfg['n_heads'], cfg['n_kv'], 1.0, delta)
                hit += combined(pr, g, rng, 400)['p'] < ALPHA_REPORTED
            row[str(delta)] = hit / 40
            print(f'    {model:<14} delta {delta:.2f} sd   fires {hit / 40:.3f}')
        pw[model] = row
    out['power_curve'] = pw

    # ---------- the real data. NUMBERS ONLY. ----------
    print('\n  OBSERVED  eta squared explained by the KV-group partition')
    print(f'    {"cell":<34}{"mean eta2":<12}{"sum":<10}{"null med":<11}{"p":<11}n_layers')
    res = {}
    for model, cfg in GQA.items():
        g = groups(cfg['n_heads'], cfg['n_kv'])
        for support in ('I_final', 'I_all'):
            for absolute in (False, True):
                pr = load(model, support, absolute)
                if pr is None:
                    continue
                key = f'{model}|{support}|{"abs" if absolute else "signed"}'
                c = combined(pr, g, rng)
                per = [layer_test(v, g, rng, 2000) for v in pr]
                hi = sum(1 for x in per if x and x['group_means']['0'] > x['group_means']['1'])
                c['n_layers_group0_larger'] = hi
                c['per_layer'] = per
                res[key] = c
                print(f'    {key:<34}{c["mean_eta_sq"]:<12.5f}{c["sum_eta_sq"]:<10.3f}'
                      f'{c["null_median"]:<11.3f}{c["p"]:<11.6f}{c["n_layers"]}')
                print(f'      null expectation for eta2 is {c["null_expected_eta_sq"]:.5f} '
                      f'((k-1)/(n-1)), so the EXCESS is '
                      f'{c["excess_eta_sq_over_null"]:.5f}')
                print(f'      layers where group 0 mean exceeds group 1: {hi} of {c["n_layers"]}')
    out['observed'] = res

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r25_kv_group.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    print('  NO VERDICT IS EMITTED. The decision threshold is not this file\'s to choose.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
