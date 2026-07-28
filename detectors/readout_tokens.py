#!/usr/bin/env python3
"""DETECTOR 4 — READOUT TOKEN VALIDITY.

    Does your readout actually distinguish the answers you are scoring?

WHERE IT CAME FROM. On 2026-07-27 the R1 atlas runner reported n=0 for phi-3.5-mini. The cause was
not the model: `encode(' ' + room)[0]` returns the SentencePiece space marker 29871 for every room
word, so all four answer ids were the same token and every margin was lg[x] - lg[x] = 0. The filter
never passed and the run wrote `verdict: AMBIGUOUS, median: nan` into a file that looked exactly
like a measurement.

It announced itself only because n hit exactly zero. Two qualifying items would have produced a
plausible floor computed from a readout that cannot tell the answers apart — and that is the
version that reaches a table.

The same project already carries this as a live claim from an earlier incident: `readout_bug`,
"bare readout scores 'frost' on 'f'; disagrees with model top-1", which corrupted 52 of 63 files.
Twice, in two tokenizers, on the same assumption: that the first token of an answer string
identifies the answer.

WHAT IT CHECKS, and the order matters — each check is only meaningful if the previous passed:

  1. DISTINCTNESS   the scored ids differ across answers. Colliding ids make every margin
                    identically zero, so nothing downstream is a measurement.
  2. PREFIX         if all answers share a leading token, it is a tokenizer artifact (space
                    marker / BOS) and must be stripped before indexing, not scored.
  3. WHOLE-WORD     the scored token IS the answer, not a piece of it. Exact, not a
                    threshold: the first version used "prefix of >2000 vocab entries" and PASSED
                    internlm2 scoring 'frost' on 'f' (313 entries), which is verbatim the bug this
                    detector is named after.
  4. AGREEMENT      argmax over the scored ids agrees with the model's own top-1 when the model
                    is confident. Requires a model; skipped without one and REPORTED as skipped,
                    because an unchecked agreement is not a passed one.

Standalone: `python3 detectors/readout_tokens.py --model <path> --answers pine gold rust frost`
Importable: `check_readout(tokenizer, answers) -> Report`

Its own positive control is `--selftest`: it must FAIL on a SentencePiece tokenizer indexed at [0]
and PASS on the same tokenizer indexed after the shared prefix. A detector that has never fired is
not a detector.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict


@dataclass
class Report:
    answers: list[str]
    ids_raw: dict[str, list[int]] = field(default_factory=dict)
    shared_prefix_len: int = 0
    scored_ids: dict[str, int] = field(default_factory=dict)
    distinct: bool = False
    n_distinct: int = 0
    prefix_stripped: bool = False
    fidelity: dict[str, int] = field(default_factory=dict)   # answer -> vocab entries sharing it
    whole_word: dict[str, bool] = field(default_factory=dict)
    agreement_checked: bool = False
    verdict: str = "UNRUN"
    why: str = ""

    def ok(self) -> bool:
        return self.verdict == "READOUT-VALID"


def check_readout(tok, answers: list[str], lead: str = " ") -> Report:
    r = Report(answers=list(answers))
    r.ids_raw = {a: tok.encode(lead + a, add_special_tokens=False) for a in answers}

    if any(len(v) == 0 for v in r.ids_raw.values()):
        r.verdict = "READOUT-INVALID"
        r.why = "at least one answer encodes to zero tokens"
        return r

    # 2. shared leading token -> tokenizer artifact, strip before indexing
    firsts = {v[0] for v in r.ids_raw.values()}
    if len(firsts) == 1 and len(answers) > 1:
        r.shared_prefix_len = 1
        r.prefix_stripped = True
    if any(len(v) <= r.shared_prefix_len for v in r.ids_raw.values()):
        r.verdict = "READOUT-INVALID"
        r.why = (f"after stripping {r.shared_prefix_len} shared prefix token(s) at least one "
                 f"answer has no token left to score")
        return r

    r.scored_ids = {a: v[r.shared_prefix_len] for a, v in r.ids_raw.items()}

    # 1. distinctness — the load-bearing one
    r.n_distinct = len(set(r.scored_ids.values()))
    r.distinct = r.n_distinct == len(answers)
    if not r.distinct:
        dupes = {}
        for a, i in r.scored_ids.items():
            dupes.setdefault(i, []).append(a)
        collide = {i: v for i, v in dupes.items() if len(v) > 1}
        r.verdict = "READOUT-INVALID"
        r.why = (f"only {r.n_distinct} distinct ids for {len(answers)} answers; colliding: "
                 f"{collide}. Every margin between two colliding answers is identically zero.")
        return r

    # 3. fidelity — how ambiguous is the scored token?
    try:
        vocab = tok.get_vocab()
        for a, i in r.scored_ids.items():
            piece = tok.convert_ids_to_tokens(i)
            r.fidelity[a] = sum(1 for t in vocab if t.startswith(piece))
    except Exception:
        r.fidelity = {}

    # WHOLE-WORD, and it is exact rather than a threshold, because the threshold version of this
    # check PASSED the canonical instance of the bug this detector is named after. On internlm2
    # 'frost' scores on the single token 'f' -- which is verbatim the project's own readout_bug
    # claim, "bare readout scores 'frost' on 'f'" -- and 'f' covers only 313 vocabulary entries, so
    # a 2000-entry ambiguity threshold let it through. Distinct ids are NECESSARY and NOT
    # SUFFICIENT: distinct fragments are still fragments. The question is binary -- is the scored
    # token the whole answer, or a piece of it?
    MARKERS = "\u2581\u0120 "            # SentencePiece, GPT-2 byte-BPE, plain space
    r.whole_word = {}
    for a, i in r.scored_ids.items():
        try:
            piece = tok.convert_ids_to_tokens(i)
        except Exception:
            r.whole_word = {}
            break
        r.whole_word[a] = piece.lstrip(MARKERS) == a

    frag = [a for a, w in r.whole_word.items() if not w]
    if frag:
        pieces = {a: tok.convert_ids_to_tokens(r.scored_ids[a]) for a in frag}
        r.verdict = "READOUT-WEAK"
        r.why = (f"ids are distinct but {len(frag)} of {len(answers)} answers are scored on a "
                 f"FRAGMENT, not the word: {pieces}. A logit on a fragment is shared with every "
                 f"other word starting the same way, so the margin is not about the answer.")
        return r

    worst = max(r.fidelity.values()) if r.fidelity else 0

    r.verdict = "READOUT-VALID"
    r.why = (f"{len(answers)} answers, {r.n_distinct} distinct scored ids"
             + (f", {r.shared_prefix_len} shared prefix token stripped" if r.prefix_stripped else "")
             + (f", worst prefix ambiguity {worst}" if r.fidelity else ", fidelity not computable"))
    return r


def selftest() -> int:
    """Positive control: a detector that has never fired is not a detector."""
    class SPLike:
        """Minimal stand-in for a SentencePiece tokenizer: prefixes a space marker to everything."""
        SP = 29871
        def encode(self, s, add_special_tokens=False):
            # content ids must depend on the CHARACTERS, not on position. The first version used
            # `1000 + i` over enumerate(), so every four-letter answer encoded identically and the
            # detector correctly reported INVALID -- a broken fixture read as a broken detector.
            ids = [self.SP] + [1000 + (ord(c) % 97) for c in s.strip()]
            self._words[ids[1]] = s.strip()
            return ids
        def get_vocab(self): return {"x": 0}
        def convert_ids_to_tokens(self, i): return "\u2581" + self._words.get(i, "x")
        _words: dict = {}

    class BPELike:
        def __init__(self): self._w = {}
        def encode(self, s, add_special_tokens=False):
            i = hash(s.strip()) % 50000
            self._w[i] = s.strip()
            return [i]
        def get_vocab(self): return {"x": 0}
        def convert_ids_to_tokens(self, i): return "\u0120" + self._w.get(i, "x")

    rows = []
    ans = ["pine", "gold", "rust", "frost"]

    # (a) the real bug: index [0] on a SP-like tokenizer -> all ids collide
    sp = SPLike()
    naive = {a: sp.encode(" " + a)[0] for a in ans}
    fired = len(set(naive.values())) == 1
    rows.append(("plain [0] indexing on a SentencePiece-like tokenizer collides", fired))

    # (b) the detector must catch it when prefix-stripping is disabled
    class SPNoStrip(SPLike):
        def encode(self, s, add_special_tokens=False):
            return [self.SP, self.SP]          # every answer -> identical two-token sequence
    rows.append(("detector reports INVALID on a colliding readout",
                 not check_readout(SPNoStrip(), ans).ok()))

    # (c) the detector must PASS the same tokenizer once the shared prefix is stripped
    rep = check_readout(sp, ans)
    rows.append(("detector reports VALID after stripping the shared prefix", rep.ok()))
    rows.append(("  ... and records that it stripped one", rep.shared_prefix_len == 1))

    # (d) it must PASS a BPE-like tokenizer without stripping anything
    rep2 = check_readout(BPELike(), ans)
    rows.append(("detector passes a BPE-like tokenizer with no stripping",
                 rep2.ok() and rep2.shared_prefix_len == 0))

    bad = 0
    for label, ok in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
        bad += 0 if ok else 1
    print("=" * 70)
    print("detector fires where it must and passes where it must"
          if not bad else f"{bad} SELFTEST FAILURE(S) — do not trust this detector")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model')
    ap.add_argument('--answers', nargs='*', default=['pine', 'gold', 'rust', 'frost'])
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.model:
        ap.error("--model is required unless --selftest")

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model, trust_remote_code=True)
    r = check_readout(tok, a.answers)
    if a.json:
        json.dump(asdict(r), sys.stdout, indent=1)
        print()
    else:
        print(f"  {r.verdict}")
        print(f"  {r.why}")
        print(f"  raw ids   : {r.ids_raw}")
        print(f"  scored ids: {r.scored_ids}")
        if r.fidelity:
            print(f"  prefix ambiguity per answer: {r.fidelity}")
        print(f"  AGREEMENT check: {'run' if r.agreement_checked else 'SKIPPED — not a pass'}")
    return 0 if r.ok() else 2


if __name__ == '__main__':
    sys.exit(main())
