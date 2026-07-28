#!/usr/bin/env python3
"""R19 -- crossed position x intervention-support exhaustive scan.

Built to R19_crossed_position_support/PREREGISTRATION.md, which was committed and gate-checked
before this file existed.

WHAT THIS MEASURES, NAMED PROPERLY. Two interventions on the same head, exhaustively:

    I_final(L,h) :  x[row, -1, h*HD:(h+1)*HD] = 0     the FINAL-QUERY head-output knockout
    I_all(L,h)   :  x[row,  :, h*HD:(h+1)*HD] = 0     the total head-output knockout

Every earlier round in this repository measured only the first and called it "ablating a head".
At the LAST layer they coincide, because nothing downstream re-reads other positions. Earlier they
need not, and the gap eta_h = tau_all - tau_final has never been measured here.

WHY THE DATASET IS BUILT RATHER THAN DRAWN. R13 found the original task is fixed-position retrieval:
the query is always Alice and Alice's line is always index 0. R15 shuffled once, which confounds
position with everything else a single permutation happens to do. Here position is CROSSED with
semantic instance: 64 base bindings, each rendered at all 8 query-line positions, twice under
different nuisance permutations of the other seven lines. Within a base instance the binding, the
query and the answer are IDENTICAL across all 16 prompts; only the queried fact's line index moves.

THE STATISTICAL UNIT IS THE BASE INSTANCE, n=64, NOT 1024 PROMPTS. Per-base aggregates are written
so a cluster bootstrap is possible downstream. Treating 1024 as independent is the error the
pre-registration exists to forbid.

NO PADDING. Prompts are grouped by exact token length and batched within a group. Every prompt in a
base instance is a permutation of the same lines, so lengths agree by construction; across base
instances they may not. Padding would put `x[row, -1, :]` on a pad token under right-padding and
would make `I_all` zero pad positions under left-padding -- both silent, neither an error.

THREE METRICS, NEVER MERGED. Signed margin, room-set KL over the 4 candidates, behavioural flip.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import sys
_HERE_F = Path(__file__).resolve()
_ROOT_F = next(p for p in _HERE_F.parents if (p / "Makefile").exists())
sys.path.insert(0, str(_ROOT_F))
_PRODUCER = str(_HERE_F.relative_to(_ROOT_F))
_CODE_VERSION = hashlib.sha256(_HERE_F.read_bytes()).hexdigest()[:8]

from task import PERSONS, OBJECTS, ROOMS          # noqa: E402
from detectors.readout_tokens import check_readout  # noqa: E402

torch.set_num_threads(20)

N_BASE = 64
N_POS = len(PERSONS)
N_NUISANCE = 2
BUILD_SEED = 20260728


def build_binding(rng, rooms):
    """person -> (object, room). Each room used exactly twice across the 8 persons."""
    ps, obs = list(PERSONS), list(OBJECTS)
    assigned = (list(rooms) * 4)[:len(ps)]
    rng.shuffle(ps)
    rng.shuffle(obs)
    rng.shuffle(assigned)
    return {ps[i]: (obs[i], assigned[i]) for i in range(len(ps))}


def line_order(query, position, base_id, replicate):
    """An ordering of the 8 persons with `query` at index `position`.

    The other seven are placed by a CYCLIC rotation of the remaining list, offset by
    (base_id, replicate). A rotation rather than a fresh shuffle so that across the 8 positions of
    one base instance the non-query lines move as little as possible -- position is the variable
    under study and the rest is nuisance, not extra noise.
    """
    others = [p for p in PERSONS if p != query]
    k = (base_id * 3 + replicate * 5) % len(others)
    rot = others[k:] + others[:k]
    return rot[:position] + [query] + rot[position:]


def render(binding, order, query):
    lines = [f"{p} owns the {binding[p][0]}. The {binding[p][0]} is in the {binding[p][1]} room."
             for p in order]
    return '\n'.join(lines + [f"Question: Which room should {query} go to find their object?",
                              "Answer: The"])


def build_dataset(rooms, eligible):
    """64 base instances x 8 positions x 2 nuisance permutations = 1024 prompts.

    `eligible` is the set of persons whose name is a single content token on THIS tokenizer; the
    query is balanced over it rather than over all of PERSONS, because a multi-token query name
    changes what the final position even is.
    """
    rng = random.Random(BUILD_SEED)
    elig = [p for p in PERSONS if p in eligible]
    if len(elig) < 2:
        return None, elig
    items = []
    for b in range(N_BASE):
        binding = build_binding(rng, rooms)
        query = elig[b % len(elig)]
        # BALANCE THE ANSWER. Without this the correct room follows the random binding and comes out
        # 320/272/256/176 across the four -- an uncontrolled answer prior, which is exactly the
        # confound that lets an answer-side logit bias masquerade as a binding effect. Force the
        # query's room to cycle, by SWAPPING room assignments with a person who already holds the
        # wanted one, so each room is still used exactly twice per instance.
        want = rooms[b % len(rooms)]
        if binding[query][1] != want:
            donor = next(p for p in binding if binding[p][1] == want)
            qo, qr = binding[query]
            do, dr = binding[donor]
            binding[query] = (qo, dr)
            binding[donor] = (do, qr)
        assert binding[query][1] == want
        assert sorted(r for _, r in binding.values()) == sorted(list(rooms) * 2)
        for pos in range(N_POS):
            for rep in range(N_NUISANCE):
                order = line_order(query, pos, b, rep)
                assert order.index(query) == pos, "position assertion -- the whole design"
                assert sorted(order) == sorted(PERSONS), "order must be a permutation"
                items.append({'base': b, 'pos': pos, 'rep': rep, 'query': query,
                              'room': binding[query][1], 'text': render(binding, order, query)})
    return items, elig


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


def main():
    global N_BASE
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--out', default='results/r19_crossed')
    ap.add_argument('--rooms', nargs='*', default=None)
    ap.add_argument('--dtype', default='float32', choices=['float32', 'bfloat16'])
    ap.add_argument('--batch', type=int, default=32)
    ap.add_argument('--n-base', type=int, default=N_BASE, help='smoke-test override')
    args = ap.parse_args()

    N_BASE = args.n_base
    rooms = list(args.rooms) if args.rooms else list(ROOMS)
    out_path = f'{args.out}_{args.tag}.json'
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    def refuse(verdict, why, **extra):
        json.dump({'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag,
                   'verdict': verdict, 'why': why, **extra},
                  open(out_path, 'w'), indent=2)
        raise SystemExit(f'REFUSED: {why} -> {out_path}')

    tok = AutoTokenizer.from_pretrained(args.model)
    dt = torch.float32 if args.dtype == 'float32' else torch.bfloat16
    m = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=dt, device_map='cuda')
    m.eval()

    rep = check_readout(tok, rooms)
    print(f'  readout detector: {rep.verdict} -- {rep.why}')
    if not rep.ok():
        refuse('REFUSED-BAD-READOUT', rep.why, readout_verdict=rep.verdict, rooms=rooms)

    def content_ids(s):
        return tok.encode(' ' + s, add_special_tokens=False)

    room_ids = {r: content_ids(r) for r in rooms}
    firsts = {ids[0] for ids in room_ids.values()}
    prefix_len = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[prefix_len] for r, ids in room_ids.items()}
    if len(set(rid.values())) != len(rid):
        refuse('REFUSED-COLLIDING-READOUT', f'room readout tokens collide: {rid}', rooms=rooms)

    eligible = {p for p in PERSONS if len(content_ids(p)) == 1 + prefix_len}
    items, elig = build_dataset(rooms, eligible)
    if items is None:
        refuse('REFUSED-NO-QUERY-NAMES',
               f'fewer than two single-token person names on this tokenizer: {sorted(eligible)}')
    print(f'  dataset: {len(items)} prompts = {N_BASE} base x {N_POS} pos x {N_NUISANCE} rep; '
          f'query balanced over {len(elig)} eligible names {elig}')

    enc = [tok(it['text'], return_tensors='pt') for it in items]
    for it, e in zip(items, enc):
        it['len'] = int(e['input_ids'].shape[1])
    # NO PADDING: group by exact token length.
    groups = {}
    for i, it in enumerate(items):
        groups.setdefault(it['len'], []).append(i)
    batches = []
    for ln, idxs in sorted(groups.items()):
        for s in range(0, len(idxs), args.batch):
            batches.append(idxs[s:s + args.batch])
    print(f'  {len(groups)} distinct lengths -> {len(batches)} zero-padding batches '
          f'(max {max(len(b) for b in batches)})')

    def encode_batch(idxs):
        return torch.cat([enc[i]['input_ids'] for i in idxs], 0).to(m.device)

    NL = len(m.model.layers)
    cfg = m.config
    NH = getattr(cfg, 'num_attention_heads')
    HD = cfg.hidden_size // NH
    name0, _ = resolve_o_proj(m.model.layers[0])
    if name0 is None:
        refuse('REFUSED-NO-O-PROJ',
               f'cannot find the attention output projection: '
               f'{[n for n, _ in m.model.layers[0].named_children()]}')

    state = {'layer': None, 'head': None, 'scope': None}

    def mk(L):
        def pre(mod, a):
            if state['layer'] != L:
                return a
            x = a[0].clone()
            h = state['head']
            lo, hi = h * HD, (h + 1) * HD
            if state['scope'] == 'final':
                x[:, -1, lo:hi] = 0
            else:
                x[:, :, lo:hi] = 0
            return (x,) + a[1:]
        return pre

    for L in range(NL):
        nm, proj = resolve_o_proj(m.model.layers[L])
        if nm != name0:
            refuse('REFUSED-NONUNIFORM-STACK',
                   f'layer {L} exposes {nm}, layer 0 exposes {name0}')
        proj.register_forward_pre_hook(mk(L))
    print(f'  hooked {NL}/{NL} layers at .{name0}   NH={NH} HD={HD}')

    order_rooms = list(rooms)
    ridx = torch.tensor([rid[r] for r in order_rooms], device=m.device)

    def readout(logits):
        """logits: (B, V) at the final position -> (margin, logprobs over the 4 rooms, argmax)."""
        sub = logits[:, ridx]
        lp = torch.log_softmax(sub.float(), dim=-1)
        return sub, lp

    # ---- baseline pass. Everything a metric needs is precomputed PER BATCH as tensors, because
    # the scan runs 336 x 2 x len(batches) forwards and a per-row Python loop inside it would cost
    # more than the model does.
    prep = []
    base_acc_n = 0
    with torch.no_grad():
        state['layer'] = None
        for bidx in batches:
            ids = encode_batch(bidx)
            lg = m(input_ids=ids, use_cache=False).logits[:, -1]
            sub, lp = readout(lg)
            c = torch.tensor([order_rooms.index(items[i]['room']) for i in bidx], device=m.device)
            masked = sub.clone()
            masked.scatter_(1, c[:, None], float('-inf'))
            bm = sub.gather(1, c[:, None])[:, 0] - masked.max(1).values
            arg = sub.argmax(1)
            base_acc_n += int((arg == c).sum())
            prep.append({'ids': ids, 'c': c, 'bm': bm, 'blp': lp, 'bp': lp.exp(), 'barg': arg,
                         'pos': torch.tensor([items[i]['pos'] for i in bidx], device=m.device),
                         'base': torch.tensor([items[i]['base'] for i in bidx], device=m.device),
                         'idx': bidx})
    acc = base_acc_n / len(items)
    base_margin = torch.cat([b['bm'] for b in prep]).tolist()
    base_pos = [items[i]['pos'] for b in prep for i in b['idx']]
    base_ok = torch.cat([(b['barg'] == b['c']) for b in prep]).tolist()
    print(f'  baseline accuracy {acc:.4f}   mean margin '
          f'{sum(base_margin) / len(base_margin):+.4f}')
    # NO CORRECTNESS FILTER, per R15's finding that filtering selects on position.

    # ---- the scan
    n_cells_per_scope = len(items)
    flips = {'final': 0, 'all': 0}
    res = {}
    Z = torch.zeros
    for L in range(NL):
        for h in range(NH):
            for scope in ('final', 'all'):
                state.update(layer=L, head=h, scope=scope)
                sp = Z(3, N_POS, device=m.device)
                sb = Z(3, N_BASE, device=m.device)
                np_ = Z(N_POS, device=m.device)
                nb_ = Z(N_BASE, device=m.device)
                nflip = 0
                with torch.no_grad():
                    for b in prep:
                        lg = m(input_ids=b['ids'], use_cache=False).logits[:, -1]
                        sub, lp = readout(lg)
                        masked = sub.clone()
                        masked.scatter_(1, b['c'][:, None], float('-inf'))
                        am = sub.gather(1, b['c'][:, None])[:, 0] - masked.max(1).values
                        d = b['bm'] - am
                        kl = (b['bp'] * (b['blp'] - lp)).sum(1)
                        fl = (sub.argmax(1) != b['barg']).float()
                        nflip += int((am < 0).sum())
                        for k, v in enumerate((d, kl, fl)):
                            sp[k].index_add_(0, b['pos'], v.float())
                            sb[k].index_add_(0, b['base'], v.float())
                        one = torch.ones_like(d, dtype=torch.float32)
                        np_.index_add_(0, b['pos'], one)
                        nb_.index_add_(0, b['base'], one)
                state['layer'] = None
                flips[scope] += nflip
                mp = (sp / np_.clamp(min=1)).cpu().tolist()
                mb = (sb / nb_.clamp(min=1)).cpu().tolist()
                res[f'L{L:02d}H{h:02d}.{scope}'] = {
                    'pos': [[round(mp[k][j], 7) for k in range(3)] for j in range(N_POS)],
                    'base': [[round(mb[k][j], 7) for k in range(3)] for j in range(N_BASE)]}
        print(f'  layer {L + 1}/{NL} done', flush=True)

    n_flip_all, n_flip_final = flips['all'], flips['final']
    n_cells = 2 * NL * NH * n_cells_per_scope

    fr_all = n_flip_all / (NL * NH * n_cells_per_scope)
    print(f'  saturation: all-position sign flips {100 * fr_all:.1f}% '
          f'(pre-registered refusal at >50%)')
    if fr_all > 0.50:
        refuse('REFUSED_SATURATED',
               f'{100 * fr_all:.1f}% of all-position cells flip the margin sign; a saturated '
               f'instrument cannot rank', flip_rate_all=fr_all)

    json.dump({'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag,
               'verdict': 'MEASURED', 'design': 'crossed position x intervention support',
               'n_layers': NL, 'n_heads_per_layer': NH, 'head_dim': HD,
               'n_base': N_BASE, 'n_positions': N_POS, 'n_nuisance': N_NUISANCE,
               'n_prompts': len(items), 'build_seed': BUILD_SEED,
               'statistical_unit': 'base instance (n=%d), NOT prompt' % N_BASE,
               'rooms': order_rooms, 'eligible_query_names': elig,
               'baseline_accuracy': acc,
               'baseline_margin_mean': sum(base_margin) / len(base_margin),
               'baseline_margin_by_pos': [
                   sum(base_margin[i] for i in range(len(base_pos)) if base_pos[i] == p)
                   / max(1, base_pos.count(p)) for p in range(N_POS)],
               'baseline_accuracy_by_pos': [
                   sum(base_ok[i] for i in range(len(base_pos)) if base_pos[i] == p)
                   / max(1, base_pos.count(p)) for p in range(N_POS)],
               'flip_rate_all': fr_all,
               'flip_rate_final': n_flip_final / (NL * NH * n_cells_per_scope),
               'metrics': ['signed_margin_drop', 'room_set_kl', 'behavioural_flip'],
               'cells': res},
              open(out_path, 'w'), indent=1)
    print(f'  wrote {out_path}')


if __name__ == '__main__':
    raise SystemExit(main())
