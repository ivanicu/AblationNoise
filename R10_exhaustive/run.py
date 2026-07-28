#!/usr/bin/env python3
"""R10 - EVERY HEAD, NO SAMPLING, IN THE VOCABULARY THE PUBLISHED EFFECTS WERE MEASURED IN.

THE CLAIM UNDER ATTACK is the repository's most striking sentence: the independently proven copy
head L22H7 moves the margin by -0.132, and the floor is 0.442, so even it is inside the noise.

THE FLOOR IN THAT SENTENCE IS POOLED OVER FOURTEEN LAYERS. R9 measured the per-layer spread and
found neighbouring layers differing tenfold -- so a band-wide draw mixes "which head" with "which
layer", and a head's effect may be being compared against a spread that is mostly between-layer
structure rather than head choice.

    W_POOLED     the band-wide floor is the right one; a head's effect belongs against "any head in
                 the retrieval band". L22H7 stays inside.
    W_LAYERWISE  between-layer variation is STRUCTURE, not noise about which head. L22H7 belongs
                 against L22's OWN spread -- and may clear it.

THE CONFOUND, WRITTEN BEFORE THE RUN: within one layer there are only NH heads, so 30 sampled
draws would be sampling with replacement from twelve objects and the sd would be dominated by
repeats. THE CONTROL REMOVES IT RATHER THAN MEASURING IT: at k=1 inside a layer there is nothing to
sample. Ablate EVERY head, once. NL x NH ablations, exact, no sampling error anywhere.

That also removes R9's sampling noise from the depth curve, so this round SUBSUMES R9 rather than
sitting beside it -- the same discipline that made R6's and R7's zero arms reproduce R1 exactly.

VOCABULARY: the ORIGINAL rooms, because that is what the eight published effects were measured in
and Amendment 2 established the floor moves 1.7x when the four nouns change. Comparing an effect to
a floor from a different vocabulary is the mismatch this file exists to avoid.

    DECIDES-LAYERWISE   |−0.132| clears 2 sd of L22's own twelve heads
    STAYS-POOLED        it does not
    and the same test is reported for all eight published effects against their own layers.

POSITIVE CONTROL, named before the run: every layer's twelve ablations must not be identical. A
layer whose heads all produce the same drop has sd 0, and its "floor" would be zero by arithmetic.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from task import PERSONS, OBJECTS, ROOMS

torch.set_num_threads(20)

SET_SIZES = [1]   # R9 sweeps DEPTH, not set size
N_DRAWS = 30
N_ITEMS = 120
SEEDS = list(range(3000, 3400))
DRAW_SEED = 20260727


def bindings(seed, rooms=None):
    # `rooms` MUST be threaded through here. The first version of --rooms scored the new vocabulary
    # while this function still built the PROMPT from the module-level ROOMS, so the text would have
    # read "the pine room" while the readout scored stone/iron/glass/water — every item scored
    # against an answer that never appears in its own prompt. Caught before launch by asking what
    # ELSE reads ROOMS, not by the run failing: it would not have failed. It would have produced a
    # complete, plausible floor for a task nobody ran.
    rooms = list(ROOMS) if rooms is None else list(rooms)
    r = random.Random(seed)
    ps, obs = list(PERSONS), list(OBJECTS)
    assigned = (rooms * 4)[:len(ps)]
    r.shuffle(ps); r.shuffle(obs); r.shuffle(assigned)
    return {ps[i]: (obs[i], assigned[i]) for i in range(len(ps))}


def prompt(query, b):
    lines = [f"{p} owns the {b[p][0]}. The {b[p][0]} is in the {b[p][1]} room." for p in PERSONS]
    return '\n'.join(lines + [f"Question: Which room should {query} go to find their object?",
                              "Answer: The"])


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--band', default='', help='LO:HI layer band to draw from; default = upper half')
    ap.add_argument('--out', default='results/r10_exhaustive')
    ap.add_argument('--rooms', nargs='*', default=None)
    ap.add_argument('--dtype', default='float32', choices=['float32','bfloat16'])
    ap.add_argument('--sizes', nargs='*', type=int, default=None,
                    help='restrict the set-size sweep; ratio_k1 needs only k=1')
    ap.add_argument('--max-gpu', default='', help="e.g. 13GiB -- spill the rest to CPU")
    args = ap.parse_args()
    rooms = args.rooms if args.rooms else list(ROOMS)
    sizes = args.sizes if args.sizes else SET_SIZES

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    load_kw = dict(trust_remote_code=True, torch_dtype=getattr(torch, args.dtype),
                   attn_implementation='eager')
    if args.max_gpu and torch.cuda.is_available():
        # An 8B in bf16 is 15 GB and the card is 15.47 GB, so it OOMs by ~20 MiB with activations.
        # Spilling the tail layers to CPU keeps the forward hooks intact -- they are registered on
        # modules, not on devices -- at the cost of some PCIe traffic per forward.
        load_kw.update(device_map='auto', max_memory={0: args.max_gpu, 'cpu': '40GiB'})
    else:
        load_kw.update(device_map='cuda' if torch.cuda.is_available() else 'cpu')
    m = AutoModelForCausalLM.from_pretrained(args.model, **load_kw).eval()
    # phi-3.5 and internlm2 ship their own modeling code, which calls DynamicCache.from_legacy_cache
    # -- an API removed in the installed transformers. Nothing here generates, so the cache is
    # written and never read; disabling it sidesteps the vendored code path without patching it.
    # Verified a no-op on Qwen before adopting rather than assumed to be one.
    m.config.use_cache = False
    NL = m.config.num_hidden_layers
    NH = m.config.num_attention_heads
    HD = m.config.hidden_size // NH

    if args.band:
        lo, hi = (int(x) for x in args.band.split(':'))
    else:                                   # the band where retrieval/copy live in every model tested
        lo, hi = NL // 2, NL - 1
    sham_lo, sham_hi = 0, max(1, NL // 4)   # early layers: the SHAM arm, outside the studied band

    # THE READOUT IS TOKENIZER-DEPENDENT AND THE FIRST VERSION SILENTLY ASSUMED QWEN'S BPE.
    #
    # `encode(' ' + room)[0]` gives a distinct id per room on a BPE tokenizer. On a SentencePiece
    # one (phi-3.5) it gives the SPACE MARKER 29871 for every room, so every margin was
    # lg[29871] - lg[29871] = 0, the baseline filter never passed, and the run reported n=0. Two
    # independent causes, both the same assumption: `single-token persons` was also 0/8 there.
    #
    # This is the project's own `readout_bug` claim -- "bare readout scores 'frost' on 'f'" -- in a
    # new tokenizer. It was loud only because n hit zero. With two qualifying names it would have
    # produced n=30 of garbage and a plausible floor, which is the version that gets published.
    #
    # Fix: drop a leading token only if EVERY room shares it (that is the space marker, and on a
    # BPE tokenizer nothing is dropped, so Qwen's numbers are unchanged), then REFUSE if the
    # resulting ids still collide. Same treatment for the person filter: single CONTENT token.
    def content_ids(s: str) -> list[int]:
        return tok.encode(' ' + s, add_special_tokens=False)

    # THE READOUT DETECTOR IS A GATE, NOT A REPORT. Distinct ids are necessary and NOT
    # sufficient: with the original vocabulary internlm2 scores 'frost' on the single token
    # 'f' and phi-3.5 scores 'pine' on '_p' -- distinct, and fragments. A logit on a fragment
    # is shared with every word starting the same way, so the margin is not about the answer.
    # detectors/readout_tokens.py decides, and the run REFUSES rather than producing a floor
    # measured through a readout that cannot see the answers.
    from detectors.readout_tokens import check_readout
    rep = check_readout(tok, rooms)
    print(f'  readout detector: {rep.verdict} -- {rep.why}')
    if not rep.ok():
        Path('results').mkdir(exist_ok=True)
        out = f'{args.out}_{args.tag}.REFUSED.json'
        json.dump({'model': args.tag, 'rooms': rooms, 'verdict': 'REFUSED-BAD-READOUT',
                   'readout_verdict': rep.verdict, 'why': rep.why,
                   'scored_ids': rep.scored_ids, 'whole_word': rep.whole_word},
                  open(out, 'w'), indent=2)
        raise SystemExit(f'REFUSED: {args.tag} readout is {rep.verdict}. {rep.why} -> {out}')

    room_ids = {r: content_ids(r) for r in rooms}
    firsts = {ids[0] for ids in room_ids.values()}
    prefix_len = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[prefix_len] for r, ids in room_ids.items()}
    if len(set(rid.values())) != len(rid):
        raise SystemExit(
            f"REFUSED: {args.tag}'s room readout tokens collide even after stripping {prefix_len} "
            f"prefix token(s): {rid}. A margin between colliding ids is identically zero; no "
            f"measurement is possible with this room vocabulary on this tokenizer.")
    single = [p for p in PERSONS if len(content_ids(p)) == 1 + prefix_len]
    print(f"  readout: prefix_len={prefix_len} room_ids={rid} | single-token persons "
          f"{len(single)}/{len(PERSONS)}")
    if not single:
        raise SystemExit(
            f"REFUSED: {args.tag} has no single-token person name (prefix_len={prefix_len}); every "
            f"item would be skipped and n would be 0. Choose a name set for this tokenizer rather "
            f"than reporting a floor of nothing.")

    active: dict[int, set[int]] = {}

    def mk(L):
        def pre(mod, a):
            if L not in active:
                return a
            x = a[0].clone()
            for h in active[L]:
                x[0, -1, h * HD:(h + 1) * HD] = 0
            return (x,) + a[1:]
        return pre

    # Architectures do not agree on what the attention module or its output projection is called.
    # internlm2 crashed here on `self_attn` (its layer exposes `attention`, whose projection is
    # `wo`, not `o_proj`). Resolve by structure rather than by a guessed name, and REFUSE loudly if
    # nothing resolves -- a silent skip would leave the hooks unregistered and every ablation would
    # measure exactly zero, which is a null this script would then happily report.
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

    name0, _ = resolve_o_proj(m.model.layers[0])
    if name0 is None:
        raise SystemExit(
            f"REFUSED: cannot find the attention output projection on {args.tag}. Layer children: "
            f"{[n for n, _ in m.model.layers[0].named_children()]}. Add its name to resolve_o_proj "
            f"rather than letting the hooks go unregistered.")
    n_hooked = 0
    for L in range(NL):
        nm, proj = resolve_o_proj(m.model.layers[L])
        if nm != name0:
            raise SystemExit(f"REFUSED: layer {L} exposes {nm}, layer 0 exposes {name0} -- the "
                             f"stack is not uniform and the hook set would be inconsistent.")
        proj.register_forward_pre_hook(mk(L))
        n_hooked += 1
    assert n_hooked == NL, f"hooked {n_hooked} of {NL} layers"
    print(f"  hooked {n_hooked}/{NL} layers at .{name0}")

    # EXHAUSTIVE. Every head, once. No seed appears here because nothing is sampled.
    conds: dict[str, list[tuple[int, int]]] = {}
    for L in range(NL):
        for h in range(NH):
            conds[f'L{L:02d}H{h:02d}'] = [(L, h)]

    def margin(enc, cor):
        lg = m(**enc, use_cache=False).logits[0, -1]
        return lg[rid[cor]].item() - max(lg[rid[r]].item() for r in rooms if r != cor)

    base: list[float] = []
    drops: dict[str, list[float]] = {k: [] for k in conds}
    n = 0
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
        bm = lg[rid[cor]].item() - max(lg[rid[r]].item() for r in rooms if r != cor)
        base.append(bm)
        for name, heads in conds.items():
            active.clear()
            for (L, h) in heads:
                active.setdefault(L, set()).add(h)
            drops[name].append(bm - margin(enc, cor))
        active.clear()
        n += 1
        if n >= N_ITEMS:
            break

    # A VERDICT ON ZERO DATA IS THE DEFECT THIS PROJECT IS ABOUT, AND THE SCRIPT COMMITTED IT.
    # phi-3.5-mini collected n=0 items -- every one failed the baseline-correct filter -- and this
    # script happily wrote `verdict: AMBIGUOUS, median: nan` into a result file that looks exactly
    # like a measurement. It was caught by reading `n`, not by anything here. A run that cannot
    # measure must REFUSE, loudly, and must not leave an artifact a later reader could mistake for
    # a cell of the atlas.
    MIN_ITEMS = 30
    if n < MIN_ITEMS:
        Path('results').mkdir(exist_ok=True)
        out = f"{args.out}_{args.tag}.REFUSED.json"
        json.dump({'model': args.tag, 'n_items': n, 'n_seeds_tried': len(SEEDS),
                   'verdict': 'REFUSED-INSUFFICIENT-ITEMS',
                   'why': (f'only {n} of {len(SEEDS)} seeds produced an item this model answers '
                           f'correctly (need {MIN_ITEMS}); no floor can be estimated. This is a '
                           f'statement about the model/task pairing, not about the floor.')},
                  open(out, 'w'), indent=2)
        raise SystemExit(
            f"REFUSED: {args.tag} answered only {n}/{len(SEEDS)} seeds correctly (need "
            f"{MIN_ITEMS}). No verdict written to the atlas; see {out}.")

    bm = float(np.mean(base))
    layers = {}
    for L in range(NL):
        v = np.array([float(np.mean(drops[f'L{L:02d}H{h:02d}'])) for h in range(NH)])
        layers[L] = {'layer': L, 'depth_frac': L / max(1, NL - 1),
                     'mean': float(v.mean()), 'sd': float(v.std(ddof=1)),
                     'floor': float(v.std(ddof=1) / abs(bm)),
                     'min': float(v.min()), 'max': float(v.max()),
                     'per_head': {h: float(np.mean(drops[f'L{L:02d}H{h:02d}'])) for h in range(NH)}}
    sds = np.array([layers[L]['sd'] for L in range(NL)])
    n_dead = int((sds < 1e-9).sum())
    rk = lambda a: np.argsort(np.argsort(a)).astype(float)
    rho = float(np.corrcoef(rk(np.arange(NL)), rk(sds))[0, 1])
    # THE FIT IS IN LOG SPACE, AND THE FIRST VERSION WAS NOT. A straight line through the sham
    # half's sd values, extrapolated to the band's depth, returned a NEGATIVE predicted sd on two
    # of four models -- and a standard deviation cannot be negative. The excess ratio then came
    # out `nan` and the verdict fell through to AMBIGUOUS for a reason that was arithmetic, not
    # empirical. sd is positive and grows multiplicatively with depth (R4 already established the
    # floor is a power law in set size), so the trend belongs in log space, where the
    # extrapolation cannot leave the domain.
    sh = np.arange(sham_lo, sham_hi + 1)
    sh_sd = np.clip(sds[sham_lo:sham_hi + 1], 1e-12, None)
    a_, b_ = np.polyfit(sh, np.log(sh_sd), 1)
    band_layers = np.arange(lo, hi + 1)
    pred = float(np.mean(np.exp(a_ * band_layers + b_)))
    obs = float(np.mean(sds[lo:hi + 1]))
    excess = obs / pred if pred > 0 else float('nan')
    verdict = ('DEPTH-EXPLAINS-IT' if (rho >= 0.7 and excess <= 1.3) else
               'BAND-IS-EXCEPTIONAL' if excess >= 1.5 else 'AMBIGUOUS')
    cells = {f'L{L}': layers[L] for L in range(NL)}

    res = {'model': args.tag, 'n_layers': NL, 'n_heads': NH, 'band': [lo, hi],
           'sham_band': [sham_lo, sham_hi], 'n_items': n, 'n_heads_per_layer': NH, 'sampling': 'none - exhaustive',
           'draw_seed': DRAW_SEED, 'base_margin': bm, 'rooms': rooms, 'dtype': args.dtype,
           'cells': cells, 'layers': layers,
           'spearman_rho_layer_sd': rho, 'sham_fit_slope': float(a_),
           'sham_fit_intercept': float(b_), 'band_sd_observed': obs,
           'band_sd_predicted_from_sham_trend': pred, 'band_excess_over_trend': excess,
           'n_dead_layers': n_dead, 'verdict': verdict}

    print(f"\n  {args.tag}: {NL}L x {NH}H | band L{lo}-{hi} | sham L{sham_lo}-{sham_hi} "
          f"| n={n} | baseline margin {bm:.3f}\n")
    print(f"  {'layer':>6}{'depth':>7}{'mean drop':>11}{'sd':>9}{'floor':>9}   profile")
    mx = max(sds) or 1.0
    for L in range(NL):
        c = layers[L]
        zone = 'SHAM' if sham_lo <= L <= sham_hi else ('BAND' if lo <= L <= hi else '    ')
        print(f"  {L:>6}{c['depth_frac']:>7.2f}{c['mean']:>+11.4f}{c['sd']:>9.4f}"
              f"{c['floor']:>9.4f}   {zone} {'#' * int(40 * c['sd'] / mx)}")
    print(f"\n  Spearman rho(layer, sd) = {rho:+.3f}   dead layers (sd = 0): {n_dead}")
    print(f"  band sd observed {obs:.4f} vs {pred:.4f} predicted by extrapolating the SHAM "
          f"half's own trend  ->  excess {excess:.2f}x")
    print(f"  VERDICT {verdict}")

    # INHERITED FROM R1 AND IT COST A COMPLETED RUN. `Path('results').mkdir` creates a directory
    # relative to the CWD, which is not where --out points. The first R9 cell did every forward
    # pass, printed every layer, and then died on the last line with FileNotFoundError. A write
    # target must be created from the path actually being written.
    out = f"{args.out}_{args.tag}.json"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out, 'w'), indent=2, default=float)
    print(f"  -> {out}")


if __name__ == '__main__':
    main()
