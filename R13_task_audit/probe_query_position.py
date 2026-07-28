#!/usr/bin/env python3
"""Which person, and which prompt LINE, is each model actually asked about?

The runners choose the query as the first person that is a single CONTENT token under that model's
tokenizer, and every binding assigns every person -- so the query is `single[0]`, the same on every
item, and its fact sits at a FIXED line index. This probe records which one, per model, per
vocabulary, using the runners' OWN tokenization convention rather than a reimplementation of it.

    THE REIMPLEMENTATION WAS TRIED FIRST AND WAS WRONG. A quick check that dropped the
    `prefix_len` adjustment reported 0 of 8 single-token persons for phi-3.5-mini, against the 6
    the actual run had printed. The disagreement with a number the run had already emitted is the
    only reason it was caught -- the same "match rule is not the concept" defect, committed while
    investigating that exact class of defect.

Needs `transformers`; loads TOKENIZERS ONLY, no weights, no GPU.

    python3 R13_task_audit/probe_query_position.py --artifacts <dir> --out <path>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

_HERE_F = pathlib.Path(__file__).resolve()
_ROOT_F = next(p for p in _HERE_F.parents if (p / "Makefile").exists())
_PRODUCER = str(_HERE_F.relative_to(_ROOT_F))
_CODE_VERSION = hashlib.sha256(_HERE_F.read_bytes()).hexdigest()[:8]

sys.path.insert(0, str(_ROOT_F))
from task import PERSONS, ROOMS, ROOMS_SHARED  # noqa: E402

MODELS = {'qwen2.5-1.5b': 'model_qwen2.5-1.5b-instruct',
          'qwen2.5-3b': 'model_qwen2.5-3b-instruct',
          'phi-3.5-mini': 'model_phi-3.5-mini-instruct',
          'internlm2-1.8b': 'model_internlm2-chat-1.8b'}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--artifacts', required=True)
    ap.add_argument('--out', default=str(_HERE_F.parent / 'results' /
                                         'tokenizer_query_positions.json'))
    args = ap.parse_args()
    from transformers import AutoTokenizer

    rows = []
    for tag, d in MODELS.items():
        tok = AutoTokenizer.from_pretrained(f"{args.artifacts.rstrip('/')}/{d}",
                                            trust_remote_code=True)

        def ci(s, _t=tok):
            return _t.encode(' ' + s, add_special_tokens=False)

        for lab, rooms in (('original', ROOMS), ('shared', ROOMS_SHARED)):
            firsts = {ci(r)[0] for r in rooms}
            pl = 1 if len(firsts) == 1 and len(rooms) > 1 else 0
            single = [p for p in PERSONS if len(ci(p)) == 1 + pl]
            q = single[0] if single else None
            rows.append({'model': tag, 'vocabulary': lab, 'prefix_len': pl,
                         'n_single_token_persons': len(single), 'query_person': q,
                         'query_line_index': PERSONS.index(q) if q else None})
            print(f"  {tag:<16}{lab:<9}prefix {pl}  single {len(single)}/{len(PERSONS)}  "
                  f"query {q} at line {rows[-1]['query_line_index']}")

    lines = {r['query_line_index'] for r in rows}
    out = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': 'ALL',
           'rows': rows, 'n_cells': len(rows),
           'distinct_query_lines': sorted(lines),
           'uniform_across_models': len(lines) == 1,
           'the_line': sorted(lines)[0] if len(lines) == 1 else None}
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(args.out, 'w'), indent=2)
    print(f"  -> distinct query line indices across {len(rows)} cells: {sorted(lines)}")
    print(f"  -> {args.out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
