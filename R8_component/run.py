#!/usr/bin/env python3
"""R8 — IS IT THE DIRECTION RELATIVE TO THE DATA, OR WHICH COMPONENT GETS DESTROYED?

Pre-registration: PREREGISTRATION.md, committed at the parent commit of this file. Nothing in it is
changed here. This runner is R7's, transformed rather than rewritten, so the two rounds share one
measurement path and their zero arms are the same object.

R6 measured that a head's final-position output splits: x = mu + (x - mu), with the varying part
only 14-27% of ||x||. R7 showed the order mean < randdir < shrink at matched displacement and could
not say why -- two of its worlds had identical rows. The arms below separate them by WHICH PART
each destroys.

    mean           x <- mu                     destroys the item-VARYING part      ||disp|| = d
    constant_only  x <- x - (d/||mu||)*mu      destroys the item-CONSTANT part     ||disp|| = d
    shrink         x <- x*(1 - d/||x||)        destroys BOTH, in proportion        ||disp|| = d
    randdir        x <- x + d*u, ||u|| = 1     destroys NEITHER; only adds         ||disp|| = d
    zero           x <- 0                      the anchor, NOT matched             ||disp|| = ||x||

THE PRIMARY STATISTIC IS THE WITHIN-CELL ORDER of readability = |positive control| / band sd,
pre-registered as the endpoint. Every RATIO is against `zero` -- the largest perturbation and the
only arm that has not died in two rounds. `mean` is never a denominator: that is what invalidated
half of R6's and R7's cells.

THE MATCHING IS MEASURED, NOT ASSERTED, and so is the overshoot. A truncating arm whose step is
longer than the vector it truncates passes THROUGH the origin -- the displacement norm is still
exactly d, CHECK 1 still passes, and the arm is MISLABELLED rather than broken. R7 found 102 such
writes. Here a non-zero count EXCLUDES the cell from the order claim.
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
from task import PERSONS, OBJECTS  # noqa: E402

# THE RESULT FILE MUST KNOW WHICH CODE PRODUCED IT. A sibling project recorded this exact defect:
# a fix was announced while the running workers kept executing the pre-edit file, and nothing in
# the output could have shown it. Its durable fix -- stamp sha256(source) into every row -- was
# never carried here, and on 2026-07-28 an audit found 40 result files with zero provenance and
# 12 of them produced by code that has since been edited.
_HERE_F = __import__("pathlib").Path(__file__).resolve()
# A BASENAME DOES NOT IDENTIFY A FILE. `_PRODUCER = Path(__file__).name` recorded "run.py", which
# eleven rounds share, so the provenance check looked it up with a glob, took whichever came first,
# and reported that it had NOT guessed. It convicted R11's result against R6's runner. The earlier
# fix -- "read the producer from the file, do not infer it from the directory" -- was right and
# incomplete: what the file recorded could not name the object either.
_ROOT_F = next(p for p in _HERE_F.parents if (p / "Makefile").exists())
_PRODUCER = str(_HERE_F.relative_to(_ROOT_F))
_CODE_VERSION = __import__("hashlib").sha256(
    __import__("pathlib").Path(__file__).read_bytes()).hexdigest()[:8]

torch.set_num_threads(20)

K = 1
N_DRAWS = 30
N_ITEMS = 120
SEEDS = list(range(3000, 3400))
DRAW_SEED = 20260727        # identical to R1 and R6: the same 30 band head sets
RANDDIR_SEED = 20260729     # the unit vectors for the randdir arm; reported in the result file
ARMS = ('zero', 'mean', 'constant_only', 'shrink', 'randdir')
MATCHED = ('mean', 'constant_only', 'shrink', 'randdir')
TRUNCATING = ('shrink', 'constant_only')   # arms whose step can pass through the origin


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
    ap.add_argument('--out', default=str(HERE / 'results' / 'r8_component'))
    args = ap.parse_args()
    rooms = args.rooms

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        args.model, trust_remote_code=True, torch_dtype=getattr(torch, args.dtype),
        device_map='cuda' if torch.cuda.is_available() else 'cpu',
        attn_implementation='eager').eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    lo, hi = NL // 2, NL - 1
    sham_lo, sham_hi = 0, max(1, NL // 4)
    PC_LAYER = lo + (hi - lo) // 2
    dev = next(m.parameters()).device

    from detectors.readout_tokens import check_readout
    rep = check_readout(tok, rooms)
    print(f"  readout detector: {rep.verdict}")
    if not rep.ok():
        raise SystemExit(f"REFUSED: {args.tag} readout is {rep.verdict}. {rep.why}")
    rid, pl = rep.scored_ids, rep.shared_prefix_len
    single = [p for p in PERSONS if len(tok.encode(' ' + p, add_special_tokens=False)) == 1 + pl]
    if not single:
        raise SystemExit(f"REFUSED: {args.tag} has no single-token person name.")

    state = {'op': 'idle', 'arm': 'zero', 'item': 0, 'disp2': 0.0, 'ndisp': 0, 'overshoot': 0}
    active: dict[int, set[int]] = {}
    cap: dict[int, list[torch.Tensor]] = {L: [] for L in range(NL)}
    MU: dict[int, torch.Tensor] = {}        # (NH, HD) per layer
    MUN: dict[int, torch.Tensor] = {}       # (NH,) per layer: ||mu||
    D: dict[int, torch.Tensor] = {}         # (n_items, NH) per layer: ||x - mu||
    XN: dict[int, torch.Tensor] = {}        # (n_items, NH) per layer: ||x||
    U: dict[int, torch.Tensor] = {}         # (n_items, NH, HD) per layer: unit vectors

    def mk(L):
        def pre(mod, a):
            if state['op'] == 'capture':
                cap[L].append(a[0][0, -1].detach().float().cpu().clone())
                return a
            if state['op'] != 'ablate' or L not in active:
                return a
            x = a[0].clone()
            i, arm = state['item'], state['arm']
            for h in active[L]:
                sl = slice(h * HD, (h + 1) * HD)
                cur = x[0, -1, sl].float()
                if arm == 'zero':
                    new = torch.zeros_like(cur)
                elif arm == 'mean':
                    new = MU[L][h].to(cur.device)
                elif arm == 'shrink':
                    # Move TOWARD THE ORIGIN by exactly d. Scaling x by (1 - d/||x||) is the point
                    # on the segment from x to 0 at distance d, which is the zeroing direction
                    # truncated to the on-distribution arm's step length.
                    #
                    # EDGE CASE THAT WOULD CHANGE WHAT THIS ARM MEANS: if d > ||x||, the step
                    # passes THROUGH the origin and out the other side, and 'toward the origin'
                    # becomes 'past the origin, sign flipped'. The displacement norm is still
                    # exactly d, so CHECK 1 would pass and the arm would be mislabelled rather
                    # than broken -- the quiet failure. Counted and reported; on the measured
                    # data d/||x|| is 0.14-0.27, so the count is expected to be zero and a
                    # non-zero one is a fact about the model, not a bug to be clipped away.
                    ratio = (D[L][i, h] / XN[L][i, h]).item()
                    if ratio > 1.0:
                        state['overshoot'] += 1
                    new = cur * (1.0 - ratio)
                elif arm == 'constant_only':
                    # Remove the same LENGTH along the item-CONSTANT direction that `mean` removes
                    # along the varying one. Not the whole constant component: that displaces by
                    # ||mu||, which is 4-7x larger and rebuilds the magnitude confound R6 died of.
                    # Same overshoot failure mode as `shrink`, with ||mu|| in place of ||x||.
                    rc = (D[L][i, h] / MUN[L][h]).item()
                    if rc > 1.0:
                        state['overshoot'] += 1
                    new = cur - rc * MU[L][h].to(cur.device)
                else:
                    new = cur + D[L][i, h].item() * U[L][i, h].to(cur.device)
                state['disp2'] += float((new - cur).pow(2).sum())
                state['ndisp'] += 1
                x[0, -1, sl] = new.to(x.dtype)
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

    items, base = [], []
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
    print(f"  n items {n} | baseline margin {bm:.4f} | band L{lo}-{hi} | PC layer {PC_LAYER}")

    state['op'] = 'capture'
    for L in cap:
        cap[L].clear()
    for enc, _ in items:
        m(**enc, use_cache=False)
    state['op'] = 'idle'

    g = torch.Generator().manual_seed(RANDDIR_SEED)
    for L in range(NL):
        X = torch.stack(cap[L]).view(n, NH, HD)          # (n, NH, HD)
        MU[L] = X.mean(0).to(dev)                        # (NH, HD)
        MUN[L] = MU[L].norm(dim=1).clamp_min(1e-9)       # (NH,)
        D[L] = (X - X.mean(0, keepdim=True)).norm(dim=2).to(dev)
        XN[L] = X.norm(dim=2).clamp_min(1e-9).to(dev)
        u = torch.randn(n, NH, HD, generator=g)
        U[L] = (u / u.norm(dim=2, keepdim=True)).to(dev)
    print(f"  captured {NL} layers x {n} items | randdir seed {RANDDIR_SEED}")

    rng = random.Random(DRAW_SEED)
    band_pool = [(L, h) for L in range(lo, hi + 1) for h in range(NH)]
    sham_pool = [(L, h) for L in range(sham_lo, sham_hi + 1) for h in range(NH)]
    band_draws = [rng.sample(band_pool, K) for _ in range(N_DRAWS)]
    sham_draws = [rng.sample(sham_pool, min(K, len(sham_pool))) for _ in range(N_DRAWS)]
    pc_heads = [(PC_LAYER, h) for h in range(NH)]

    def sweep(heads, arm):
        state['op'], state['arm'] = 'ablate', arm
        state['disp2'], state['ndisp'], state['overshoot'] = 0.0, 0, 0
        active.clear()
        for (L, h) in heads:
            active.setdefault(L, set()).add(h)
        d = []
        for i, (enc, cor) in enumerate(items):
            state['item'] = i
            lg = m(**enc, use_cache=False).logits[0, -1]
            d.append(base[i] - (lg[rid[cor]].item()
                                - max(lg[rid[r]].item() for r in rooms if r != cor)))
        active.clear()
        state['op'] = 'idle'
        rms = (state['disp2'] / max(1, state['ndisp'])) ** 0.5
        return float(np.mean(d)), rms, state['overshoot']

    arms = {}
    for arm in ARMS:
        bv, bd, ov = [], [], 0
        for dr in band_draws:
            v, r, o = sweep(dr, arm)
            bv.append(v); bd.append(r); ov += o
        sv = np.array([sweep(dr, arm)[0] for dr in sham_draws])
        pcv, _, _ = sweep(pc_heads, arm)
        bv = np.array(bv)
        sd = float(bv.std(ddof=1))
        arms[arm] = {
            'band_sd': sd, 'band_mean': float(bv.mean()),
            'band_floor': float(sd / abs(bm)),
            'sham_sd': float(sv.std(ddof=1)),
            'sham_floor': float(sv.std(ddof=1) / abs(bm)),
            'ratio_k1': float((sd / abs(bm)) / (sv.std(ddof=1) / abs(bm)))
            if sv.std(ddof=1) else float('nan'),
            'positive_control': pcv,
            'readability': float(abs(pcv) / sd) if sd else float('nan'),
            'pc_clears_own_floor': bool(abs(pcv) > sd),
            # The realized displacement, RMS over every head-write this arm performed on the band
            # draws. Reported per arm so CHECK 1 is a measurement and not a claim about the code.
            'realized_disp_rms': float(np.mean(bd)),
            'n_overshoot_past_origin': ov,
        }
        a = arms[arm]
        print(f"  {arm:<9} band sd {sd:.5f}  floor {a['band_floor']:.5f}  "
              f"PC {pcv:+.4f} = {abs(pcv)/sd:5.2f} band-sd "
              f"{'ok' if a['pc_clears_own_floor'] else 'DEAD'}  "
              f"|disp| {a['realized_disp_rms']:.4f}"
              + (f"  OVERSHOOT {a['n_overshoot_past_origin']}"
                 if a['n_overshoot_past_origin'] else ""))

    # ── CHECK 1: the matching is real ────────────────────────────────────────────────────────
    dsp = [arms[a]['realized_disp_rms'] for a in MATCHED]
    spread = (max(dsp) - min(dsp)) / (sum(dsp) / len(dsp))
    c1 = bool(spread <= 0.01)
    print(f"\n  CHECK 1 matched arms' realized |disp|: " +
          '  '.join(f"{a} {arms[a]['realized_disp_rms']:.4f}" for a in MATCHED) +
          f"  spread {100*spread:.2f}% -> {'MATCHED' if c1 else '*** NOT MATCHED ***'}")
    print(f"          (unmatched anchor: zero {arms['zero']['realized_disp_rms']:.4f}, "
          f"{arms['zero']['realized_disp_rms']/max(dsp):.1f}x the matched step)")

    # ── CHECK 2: the zero arm reproduces R1 ──────────────────────────────────────────────────
    r1p = HERE.parent / 'R1_noise_floor' / 'results' / f'r1v3_atlas_{args.tag}.json'
    repro = {'available': r1p.exists()}
    if r1p.exists():
        c = json.load(open(r1p))['cells']
        r1r = c['band_k1']['floor'] / c['sham_k1']['floor']
        rd = abs(arms['zero']['ratio_k1'] - r1r) / r1r
        repro.update({'r1_ratio_k1': r1r, 'r7_zero_ratio_k1': arms['zero']['ratio_k1'],
                      'rel_diff': rd, 'reproduces': bool(rd <= 0.10)})
        print(f"  CHECK 2 zero arm vs R1: {r1r:.2f}x vs {arms['zero']['ratio_k1']:.2f}x "
              f"({100*rd:.1f}% apart) -> "
              f"{'REPRODUCES' if repro['reproduces'] else '*** DOES NOT REPRODUCE ***'}")

    # THE SIGN CHECK BELONGS HERE, NOT IN A REPORT. detectors/control_fitness.py was written
    # after a positive control fired INVERTED, carries a selftest that checks sign -- and until
    # 2026-07-28 no runner had ever imported it. Meanwhile randdir's control came back inverted on
    # every model of two rounds and `|PC| > sd` passed it every time, because that test is
    # magnitude-only. A detector nobody calls is not a detector.
    from detectors.control_fitness import check_control
    anchor_sign = 1 if arms['zero']['positive_control'] >= 0 else -1
    for a in ARMS:
        rep_a = check_control(positive_control=arms[a]['positive_control'],
                              positive_control_expected_sign=anchor_sign)
        arms[a]['pc_sign_matches_anchor'] = bool(
            (1 if arms[a]['positive_control'] >= 0 else -1) == anchor_sign)
        arms[a]['control_fitness_verdict'] = rep_a.verdict
        # ADMISSIBLE = the magnitude clears AND the sign points the way the anchor does. An arm
        # failing either cannot have |PC|/sd read as readability: a dead control gives a ratio of
        # two small noisy numbers, an inverted one gives a magnitude that reads as calibration
        # while the instrument is measuring something else.
        arms[a]['admissible'] = bool(arms[a]['pc_clears_own_floor']
                                     and arms[a]['pc_sign_matches_anchor'])
    inverted = [a for a in ARMS if not arms[a]['pc_sign_matches_anchor']]
    if inverted:
        print(f"  *** POSITIVE CONTROL SIGN-INVERTED vs the zero arm on: {', '.join(inverted)}"
              f" -- those arms are INADMISSIBLE, |PC| > sd passes them anyway")

    dead = [a for a in ARMS if not arms[a]['pc_clears_own_floor']]
    print(f"  CHECK 3 every arm has a live positive control: "
          f"{'PASS' if not dead else 'FAIL on ' + ', '.join(dead)}")

    # EVERY RATIO IS AGAINST `zero`. R6 and R7 both put `mean` in the denominator and both lost
    # cells to it: a dead denominator inflates a ratio without bound (R6's ratio_k1 reached 2133x).
    # `zero` is the largest perturbation available and has not died on any model in two rounds.
    rr = {a: arms[a]['readability'] / arms['zero']['readability'] for a in MATCHED}
    order = sorted(MATCHED, key=lambda a: arms[a]['readability'])
    print(f"\n  readability |PC|/band sd: " +
          '  '.join(f"{a} {arms[a]['readability']:.2f}" for a in ARMS))
    print(f"  rr vs zero: " + '  '.join(f"{k} {v:.2f}x" for k, v in rr.items()))
    print(f"  ORDER low->high: {' < '.join(order)}")

    # The two inclusion properties R6 conflated, reported separately with which one failed.
    inc_ratio = bool(arms['zero']['ratio_k1'] > 1.5)
    inc_pc = bool(arms['zero']['pc_clears_own_floor'])
    # CHECK 3: a truncating arm that overshot is MISLABELLED, not broken, so the cell keeps its
    # numbers and loses its vote on the ORDER. R7 reported the count beside the claim; that was
    # too weak -- a reader has to do the exclusion themselves, and nobody does.
    overshoot_total = sum(arms[a]['n_overshoot_past_origin'] for a in TRUNCATING)
    order_eligible = bool(inc_ratio and overshoot_total == 0)
    res = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag, 'n_items': n, 'n_draws': N_DRAWS, 'k': K, 'dtype': args.dtype,
           'band': [lo, hi], 'sham_band': [sham_lo, sham_hi], 'pc_layer': PC_LAYER,
           'rooms': rooms, 'draw_seed': DRAW_SEED, 'randdir_seed': RANDDIR_SEED,
           'base_margin': bm, 'arms': arms, 'rr': rr, 'order_low_to_high': order,
           'overshoot_total': overshoot_total, 'order_eligible': order_eligible,
           'order_ineligible_because': [] if order_eligible else
                                       ([] if inc_ratio else ['zero_ratio_k1<=1.5']) +
                                       ([] if overshoot_total == 0 else ['overshoot>0']),
           'check1_matched': c1, 'check1_spread': spread,
           'check2_zero_reproduces_r1': repro,
           'check3_dead_arms': dead,
           'inadmissible_arms': [a for a in ARMS if not arms[a]['admissible']],
           'include': bool(inc_ratio and inc_pc),
           'include_fail': [] if inc_ratio and inc_pc else
                           ([] if inc_ratio else ['zero_ratio_k1<=1.5']) +
                           ([] if inc_pc else ['zero_pc_below_own_floor']),
           'round_valid': bool(c1 and not dead and repro.get('reproduces', False))}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out = f"{args.out}_{args.tag}.json"
    json.dump(res, open(out, 'w'), indent=2, default=float)
    print(f"\n  round_valid {res['round_valid']} | order_eligible {res['order_eligible']} "
          f"{res['order_ineligible_because']} | overshoot {overshoot_total}\n  -> {out}")
    return 0 if res['round_valid'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
