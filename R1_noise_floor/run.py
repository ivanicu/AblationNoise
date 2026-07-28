#!/usr/bin/env python3
"""R1 — THE ABLATION NOISE-FLOOR ATLAS.

THE QUESTION. Interpretability papers report the effect of ablating a component (a head, a set of
heads, a layer) and read the size of that effect as evidence of localisation. Almost none report
what a RANDOM component set of the same size does. E132d measured that once, for one model at one
set size, and the answer was large: random 5-head ablation moved the correct-answer margin over a
range of 2.48 on a baseline of 4.48 — 55% of the quantity being measured, in either direction.

If that is general, a large fraction of published localisation effects are inside their own noise.
If it is not, this line dies here. R1 is the gate.

THE ESTIMAND, and it is deliberately dimensionless. Margin is in logits, whose scale differs across
models, so the raw spread is not comparable. Every cell reports

    floor = sd(null draws) / |baseline margin|

which is the fraction of the measured quantity that random component choice alone accounts for.
The MEAN of the null is reported too but is NOT the floor: ablating more components damages more on
average, and that trend is expected and uninteresting. What decides whether a reported effect is
readable is the SPREAD at its own set size.

PRE-REGISTERED GATE (written before the run, and this file is committed before results exist):

    FLOOR-IS-LARGE     median floor over cells >= 0.10   -> the thesis lives: a tenth of the
                       measured quantity is unallocated noise, and published effects must be
                       placed against it.
    FLOOR-IS-SMALL     median floor over cells <  0.03   -> published ablation effects are
                       comfortably outside random variation. The line DIES; pivot to the EM
                       object-level results.
    AMBIGUOUS          in between -> needs more models/sites before any claim.

CONTROLS IN THE SAME RUN.
  * size sweep {1,2,5,10,20} — a floor that only exists at one size is a property of that size.
  * a SHAM ablation (zero a component set OUTSIDE the layer band under study) — if the floor is the
    same there, it is a property of perturbing the model at all, not of the studied circuit.
  * baseline re-measurement per item, so drift in the item set cannot masquerade as effect.

WHAT WOULD MAKE THIS WRONG. The obvious confound: zeroing a head output is off-manifold, so a large
spread might be "any off-manifold perturbation is chaotic" rather than "component choice matters".
That is why the sham arm is in the same run. It does not rescue published claims either way — those
claims use this same off-manifold operation — but it changes what the floor is a floor OF, and the
distinction goes in the write-up rather than being discovered by a reviewer.
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

# THE RESULT FILE MUST KNOW WHICH CODE PRODUCED IT. A sibling project recorded this exact defect:
# a fix was announced while the running workers kept executing the pre-edit file, and nothing in
# the output could have shown it. Its durable fix -- stamp sha256(source) into every row -- was
# never carried here, and on 2026-07-28 an audit found 40 result files with zero provenance and
# 12 of them produced by code that has since been edited.
_CODE_VERSION = __import__("hashlib").sha256(
    __import__("pathlib").Path(__file__).read_bytes()).hexdigest()[:8]

torch.set_num_threads(20)

SET_SIZES = [1, 2, 5, 10, 20]
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
    ap.add_argument('--out', default='results/r1_null_atlas')
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

    rng = random.Random(DRAW_SEED)
    band_pool = [(L, h) for L in range(lo, hi + 1) for h in range(NH)]
    sham_pool = [(L, h) for L in range(sham_lo, sham_hi + 1) for h in range(NH)]

    conds: dict[str, list[tuple[int, int]]] = {}
    for k in sizes:
        if k > len(band_pool):
            continue
        for i in range(N_DRAWS):
            conds[f'band_k{k}_d{i:02d}'] = rng.sample(band_pool, k)
        for i in range(N_DRAWS):
            conds[f'sham_k{k}_d{i:02d}'] = rng.sample(sham_pool, min(k, len(sham_pool)))

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
    cells = {}
    for arm in ('band', 'sham'):
        for k in sizes:
            vals = [float(np.mean(drops[f'{arm}_k{k}_d{i:02d}']))
                    for i in range(N_DRAWS) if f'{arm}_k{k}_d{i:02d}' in drops]
            if not vals:
                continue
            v = np.array(vals)
            cells[f'{arm}_k{k}'] = {
                'arm': arm, 'k': k, 'n_draws': len(vals),
                'mean': float(v.mean()), 'sd': float(v.std(ddof=1)),
                'min': float(v.min()), 'max': float(v.max()),
                'floor': float(v.std(ddof=1) / abs(bm)),          # THE ESTIMAND
                'peak_to_peak_frac': float((v.max() - v.min()) / abs(bm)),
            }

    band_floors = [c['floor'] for c in cells.values() if c['arm'] == 'band']
    med = float(np.median(band_floors))
    verdict = ('FLOOR-IS-LARGE' if med >= 0.10 else
               'FLOOR-IS-SMALL' if med < 0.03 else 'AMBIGUOUS')

    res = {'code_version': _CODE_VERSION, 'code_version': _CODE_VERSION, 'model': args.tag, 'n_layers': NL, 'n_heads': NH, 'band': [lo, hi],
           'sham_band': [sham_lo, sham_hi], 'n_items': n, 'n_draws': N_DRAWS,
           'draw_seed': DRAW_SEED, 'base_margin': bm, 'rooms': rooms, 'dtype': args.dtype,
           'set_sizes_run': sizes, 'reduced_scope': sizes != SET_SIZES,
           'cells': cells, 'median_band_floor': med, 'verdict': verdict}

    print(f"\n  {args.tag}: {NL}L x {NH}H | band L{lo}-{hi} | sham L{sham_lo}-{sham_hi} "
          f"| n={n} | baseline margin {bm:.3f}\n")
    print(f"  {'cell':<12}{'mean':>9}{'sd':>8}{'range':>20}{'FLOOR':>9}{'p2p':>8}")
    for name, c in cells.items():
        rng_s = f"[{c['min']:+.2f}, {c['max']:+.2f}]"
        print(f"  {name:<12}{c['mean']:>+9.3f}{c['sd']:>8.3f}{rng_s:>20}"
              f"{c['floor']:>9.3f}{c['peak_to_peak_frac']:>8.2f}")
    print(f"\n  median floor over the studied band = {med:.3f}  ->  {verdict}")
    print("  (floor = sd(null) / baseline margin: the fraction of the measured quantity that")
    print("   random component choice alone accounts for)")

    Path('results').mkdir(exist_ok=True)
    out = f"{args.out}_{args.tag}.json"
    json.dump(res, open(out, 'w'), indent=2, default=float)
    print(f"  -> {out}")


if __name__ == '__main__':
    main()
