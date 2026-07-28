#!/usr/bin/env python3
"""R14 — baseline accuracy with the fact lines SHUFFLED, against the same seeds unshuffled.

The readings are fixed in PREREGISTRATION.md, committed before this ran. No ablation: 240 forward
passes, two arms, same items. If the model cannot do the shuffled task at all, an exhaustive scan
over it would measure nothing and must not be run.

    python3 R14_position_vs_binding/probe.py --model <hf-path> --tag <name>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

_HERE_F = pathlib.Path(__file__).resolve()
_ROOT_F = next(p for p in _HERE_F.parents if (p / "Makefile").exists())
_PRODUCER = str(_HERE_F.relative_to(_ROOT_F))
_CODE_VERSION = hashlib.sha256(_HERE_F.read_bytes()).hexdigest()[:8]

sys.path.insert(0, str(_ROOT_F))
from task import PERSONS, OBJECTS, ROOMS  # noqa: E402

torch.set_num_threads(20)
SEEDS = list(range(3000, 3400))
N_ITEMS = 120
CHANCE = 0.25
BINDING_RATIO = 0.9        # pre-registered
POSITION_CEILING = 0.35    # pre-registered: chance + 10 points


def bindings(seed, rooms):
    r = random.Random(seed)
    ps, obs = list(PERSONS), list(OBJECTS)
    assigned = (list(rooms) * 4)[:len(ps)]
    r.shuffle(ps)
    r.shuffle(obs)
    r.shuffle(assigned)
    return {ps[i]: (obs[i], assigned[i]) for i in range(len(ps))}


def build(query, b, order):
    """`order` is the sequence of persons whose facts are emitted, in emission order."""
    lines = [f"{p} owns the {b[p][0]}. The {b[p][0]} is in the {b[p][1]} room." for p in order]
    return '\n'.join(lines + [f"Question: Which room should {query} go to find their object?",
                              "Answer: The"])


@torch.no_grad()
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--rooms', nargs='*', default=list(ROOMS))
    ap.add_argument('--out', default=str(_HERE_F.parent / 'results' / 'r14_probe'))
    args = ap.parse_args()
    rooms = args.rooms

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        args.model, trust_remote_code=True, torch_dtype=torch.float32,
        device_map='cuda' if torch.cuda.is_available() else 'cpu',
        attn_implementation='eager').eval()
    m.config.use_cache = False

    from detectors.readout_tokens import check_readout
    rep = check_readout(tok, rooms)
    if not rep.ok():
        raise SystemExit(f"REFUSED: {args.tag} readout is {rep.verdict}. {rep.why}")
    rid, pl = rep.scored_ids, rep.shared_prefix_len
    single = [p for p in PERSONS if len(tok.encode(' ' + p, add_special_tokens=False)) == 1 + pl]
    if not single:
        raise SystemExit(f"REFUSED: {args.tag} has no single-content-token person.")
    q = single[0]

    def answer(text):
        enc = {k: v.to(m.device) for k, v in tok(text, return_tensors='pt').items()}
        lg = m(**enc, use_cache=False).logits[0, -1]
        return max(rooms, key=lambda r: lg[rid[r]].item())

    rows = []
    shuf = random.Random(90210)          # fixed, so the line assignment is reproducible
    for s in SEEDS:
        if len(rows) >= N_ITEMS:
            break
        b = bindings(s, rooms)
        order = list(PERSONS)
        shuf.shuffle(order)
        correct = b[q][1]
        rows.append({'seed': s, 'answer_line_shuffled': order.index(q),
                     'orig_ok': answer(build(q, b, list(PERSONS))) == correct,
                     'shuf_ok': answer(build(q, b, order)) == correct})

    n = len(rows)
    a_orig = sum(r['orig_ok'] for r in rows) / n
    a_shuf = sum(r['shuf_ok'] for r in rows) / n
    verdict = ('BINDING' if a_shuf >= BINDING_RATIO * a_orig else
               'POSITION' if a_shuf <= POSITION_CEILING else 'MIXED')

    # THE CONFOUND'S CONTROL, in the same run. Position-copying predicts a STEP -- near-perfect when
    # the answer lands at line 0, near chance elsewhere. A primacy/recency effect predicts a smooth
    # decay with distance. The same 120 items measure both, and the shapes are different.
    by_line = {}
    for r in rows:
        by_line.setdefault(r['answer_line_shuffled'], []).append(r['shuf_ok'])
    by_line = {k: {'n': len(v), 'acc': sum(v) / len(v)} for k, v in sorted(by_line.items())}

    out = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag,
           'n_items': n, 'rooms': rooms, 'query_person': q, 'chance': CHANCE,
           'accuracy_original': a_orig, 'accuracy_shuffled': a_shuf,
           'binding_ratio_threshold': BINDING_RATIO, 'position_ceiling': POSITION_CEILING,
           'verdict': verdict, 'accuracy_by_answer_line': by_line, 'rows': rows}
    print(f"  {args.tag}: query {q}, n={n}")
    print(f"    accuracy ORIGINAL (answer always at line 0) : {a_orig:.3f}")
    print(f"    accuracy SHUFFLED (answer at a random line) : {a_shuf:.3f}")
    print(f"    -> {verdict}   (BINDING if shuf >= {BINDING_RATIO}*orig; "
          f"POSITION if shuf <= {POSITION_CEILING})")
    print(f"    accuracy by the answer's line under shuffling -- a STEP means position-copying, "
          f"a smooth decay means primacy:")
    for k, v in by_line.items():
        print(f"      line {k}: {v['acc']:.2f}  (n={v['n']})")
    p = pathlib.Path(f"{args.out}_{args.tag}.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(p, 'w'), indent=2)
    print(f"  -> {p}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
