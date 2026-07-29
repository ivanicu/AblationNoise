#!/usr/bin/env python3
"""Gate 2 of R26_decomposition/PREREGISTRATION.md. Nothing downstream runs until this passes.

Gate 1 proved the downloaded TENSORS are the tensors the scans measured. That says nothing about
whether this box reproduces the same BEHAVIOUR -- tokenizer version, transformers version, attention
implementation, dtype handling and device placement have all moved since the scans ran.

So: replay R10's item loop with NO ablation hooks and reproduce `base_margin` to 4 decimals.
  qwen2.5-1.5b  4.476822
  qwen2.5-3b    6.637212

The 3b checkpoint has no frozen weight reference, so this is its ONLY identity gate and is therefore
the weaker of the two -- stated in the registration before the run, not after.

Nothing is reimplemented: `bindings`, `prompt`, PERSONS/ROOMS, the seed window, the readout-token
resolution and the baseline-correct filter are all imported or transcribed from
R10_exhaustive/run.py, which is the runner that produced the reference number.

THE GATE IS A HARD RETURN.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'R10_exhaustive'))

DECIMALS = 4
TARGETS = {'qwen2.5-1.5b': ('artifacts/model_qwen2.5-1.5b-instruct',
                            'R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json'),
           'qwen2.5-3b': ('artifacts/model_qwen2.5-3b-instruct',
                          'R10_exhaustive/results/r10_exhaustive_qwen2.5-3b.json')}


def replay(tag, model_dir, ref_path):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import run as R10                                                    # noqa: N813
    from task import PERSONS, ROOMS

    ref = json.load(open(REPO / ref_path))
    want = ref['base_margin']
    rooms = ref['rooms'] if ref.get('rooms') else list(ROOMS)
    n_items, dtype = ref['n_items'], ref['dtype']

    tok = AutoTokenizer.from_pretrained(str(REPO / model_dir), trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        str(REPO / model_dir), trust_remote_code=True,
        torch_dtype=getattr(torch, dtype), attn_implementation='eager',
        device_map='cuda' if torch.cuda.is_available() else 'cpu').eval()
    m.config.use_cache = False

    def content_ids(s):
        return tok.encode(' ' + s, add_special_tokens=False)

    room_ids = {r: content_ids(r) for r in rooms}
    firsts = {ids[0] for ids in room_ids.values()}
    prefix_len = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
    rid = {r: ids[prefix_len] for r, ids in room_ids.items()}
    single = [p for p in PERSONS if len(content_ids(p)) == 1 + prefix_len]

    base, n, skipped_no_query, skipped_wrong = [], 0, 0, 0
    with torch.no_grad():
        for s in R10.SEEDS:
            b = R10.bindings(s, rooms)
            q = next((p for p in single if p in b), None)
            if q is None:
                skipped_no_query += 1
                continue
            enc = {k: v.to(m.device) for k, v in
                   tok(R10.prompt(q, b), return_tensors='pt').items()}
            cor = b[q][1]
            lg = m(**enc, use_cache=False).logits[0, -1]
            if max(rooms, key=lambda r: lg[rid[r]].item()) != cor:
                skipped_wrong += 1
                continue
            base.append(lg[rid[cor]].item()
                        - max(lg[rid[r]].item() for r in rooms if r != cor))
            n += 1
            if n >= n_items:
                break
    got = sum(base) / len(base)
    ok = round(got, DECIMALS) == round(want, DECIMALS)
    print(f'    {tag:<14} n {n:<5} frozen {want!r}')
    print(f'    {"":<14} recomputed {got!r}   |delta| {abs(got - want):.3e}   '
          f'-> {"PASS" if ok else "FAIL"} at {DECIMALS} decimals')
    print(f'    {"":<14} items skipped: no single-token query {skipped_no_query}, '
          f'baseline wrong {skipped_wrong}')
    del m
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {'tag': tag, 'frozen_base_margin': want, 'recomputed_base_margin': got,
            'abs_delta': abs(got - want), 'decimals': DECIMALS, 'n_items': n,
            'n_items_reference': n_items, 'dtype': dtype,
            'skipped_no_single_token_query': skipped_no_query,
            'skipped_baseline_wrong': skipped_wrong, 'pass': ok}


def main():
    print('  GATE 2  behavioural identity: replay R10\'s item loop, no ablation hooks')
    out = {'gate': 'behavioural_identity', 'decimals': DECIMALS, 'models': {}}
    for tag, (md, rp) in TARGETS.items():
        if not (REPO / md).exists():
            print(f'    {tag:<14} checkpoint absent at {md} -> SKIP')
            out['models'][tag] = {'pass': False, 'reason': 'checkpoint absent'}
            continue
        out['models'][tag] = replay(tag, md, rp)
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    json.dump(out, open(HERE / 'results' / 'r26_gate2_behavioural_identity.json', 'w'), indent=1)

    p15 = out['models'].get('qwen2.5-1.5b', {}).get('pass', False)
    p3 = out['models'].get('qwen2.5-3b', {}).get('pass', False)
    if p15 and p3:
        print('\n  -> GATE 2 PASS, both checkpoints. This box reproduces the scans\' behaviour.')
        return 0
    if p15 and not p3:
        # registered before the run: run 1.5b alone, decide on its 2 strata, never pool
        print('\n  -> GATE 2 PARTIAL. 1.5b reproduces, 3b does not. Per the registration: run 1.5b '
              'alone,\n     decide on its 2 strata, and mark cross-model generality OUT OF SCOPE. '
              'Never pool.')
        return 0
    print('\n  -> STOP. The 1.5b behavioural gate failed; no number is read.')
    return 3


if __name__ == '__main__':
    sys.exit(main())
