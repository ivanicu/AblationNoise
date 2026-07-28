#!/usr/bin/env python3
"""R2 — HOW OFTEN DOES ABLATING A KNOWN MECHANISM GO THE WRONG WAY?

Pre-registration: R2_PREREGISTRATION.md, committed at e60a1c2 before this file existed.

THE ROUND-INVALIDATING CHECK RUNS FIRST (`--gate-check`): the top-k prefix-matching heads must hurt
induction AND clear 2 sd of the size-matched RANDOM null. If they do not, there is no known mechanism
here, R2 has no positive control of its own -- the very defect it investigates, one level up.
(The original criterion compared top-k to bottom-k; see R2_AMENDMENT_1_specificity.md for why that
was the same mistake R1 exists to prevent.)

A DESIGN DIFFERENCE FROM R1, STATED BECAUSE IT IS REAL AND NOT A TYPO. R1 ablates at the FINAL
POSITION only, because the binding readout is a single next-token margin there. Induction is
measured across every position of the second copy, so ablating only the last position would leave
the mechanism intact everywhere the metric looks. R2 therefore ablates at ALL positions. The two
rounds' floors are consequently not interchangeable, and R2 measures its own null rather than
borrowing R1's.

SELECTION AND OUTCOME DO NOT SHARE A DEFINITION: heads are selected by attention mass (prefix
matching), and scored by next-token log-probability. Neither is computed from the other.
"""
from __future__ import annotations

import argparse
import sys
import json
import random
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

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

T = 64              # length of one copy; the sequence is 2T
N_SEQ = 24          # random sequences
K = 5               # set size, identical across every arm
N_DRAWS = 30
DRAW_SEED = 20260727


def make_seqs(tok, n, T, seed=0):
    """Doubled random token sequences. Vocab is restricted to mid-range ids to avoid specials."""
    rng = random.Random(seed)
    lo, hi = 1000, min(tok.vocab_size - 1000, 40000)
    out = []
    for _ in range(n):
        core = [rng.randrange(lo, hi) for _ in range(T)]
        out.append(core + core)
    return out


@torch.no_grad()
def induction_scores(m, seqs, NL, NH, dev):
    """Per-head prefix-matching score: at position i in the second copy, attention to i-T+1."""
    acc = np.zeros((NL, NH))
    for s in seqs:
        ids = torch.tensor([s], device=dev)
        out = m(ids, output_attentions=True, use_cache=False)
        for L in range(NL):
            a = out.attentions[L][0]                      # (H, S, S)
            idx = torch.arange(T, 2 * T - 1, device=dev)
            tgt = idx - T + 1
            acc[L] += a[:, idx, tgt].mean(dim=1).float().cpu().numpy()
    return acc / len(seqs)


@torch.no_grad()
def induction_logprob(m, seqs, dev):
    """Mean log-prob of the true next token over the SECOND copy. Higher is better."""
    vals = []
    for s in seqs:
        ids = torch.tensor([s], device=dev)
        lg = m(ids, use_cache=False).logits[0].float().log_softmax(-1)
        tgt = torch.tensor(s[T + 1:], device=dev)
        pos = torch.arange(T, 2 * T - 1, device=dev)
        vals.append(lg[pos, tgt].mean().item())
    return float(np.mean(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='artifacts/model_qwen2.5-1.5b-instruct')
    ap.add_argument('--tag', default='qwen2.5-1.5b')
    ap.add_argument('--dtype', default='float32', choices=['float32', 'bfloat16'])
    ap.add_argument('--max-gpu', default='')
    ap.add_argument('--gate-check', action='store_true',
                    help='run only the round-invalidating check and exit')
    ap.add_argument('--out', default='results/r2_inversion')
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    kw = dict(trust_remote_code=True, torch_dtype=getattr(torch, args.dtype),
              attn_implementation='eager')
    if args.max_gpu and torch.cuda.is_available():
        kw.update(device_map='auto', max_memory={0: args.max_gpu, 'cpu': '40GiB'})
    else:
        kw.update(device_map='cuda' if torch.cuda.is_available() else 'cpu')
    m = AutoModelForCausalLM.from_pretrained(args.model, **kw).eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    dev = next(m.parameters()).device
    if str(dev) == 'meta':
        dev = torch.device('cuda')

    seqs = make_seqs(tok, N_SEQ, T, seed=7)
    scores = induction_scores(m, seqs, NL, NH, dev)
    flat = sorted(((scores[L, h], L, h) for L in range(NL) for h in range(NH)), reverse=True)
    top = [(L, h) for _, L, h in flat[:K]]
    bot = [(L, h) for _, L, h in flat[-K:]]
    print(f"  {args.tag}: {NL}L x {NH}H | induction score top {flat[0][0]:.3f} "
          f"bottom {flat[-1][0]:.4f}")
    print(f"  top-{K}: {top}")

    # ── the ablation hook: ALL positions, unlike R1's final-position-only ──────────────────
    active: dict[int, set[int]] = {}

    def mk(L):
        def pre(mod, a):
            if L not in active:
                return a
            x = a[0].clone()
            for h in active[L]:
                x[..., h * HD:(h + 1) * HD] = 0
            return (x,) + a[1:]
        return pre

    for L in range(NL):
        att = getattr(m.model.layers[L], 'self_attn', None) or m.model.layers[L].attention
        proj = getattr(att, 'o_proj', None) or getattr(att, 'wo')
        proj.register_forward_pre_hook(mk(L))

    def run(heads):
        active.clear()
        for (L, h) in heads:
            active.setdefault(L, set()).add(h)
        v = induction_logprob(m, seqs, dev)
        active.clear()
        return v

    base = run([])
    d_top = run(top) - base
    d_bot = run(bot) - base
    print(f"  baseline induction logprob {base:+.4f}")
    print(f"  ablate top-{K}:    {d_top:+.4f}   (expected NEGATIVE)")
    print(f"  ablate bottom-{K}: {d_bot:+.4f}")

    if args.gate_check:
        # AMENDED (R2_AMENDMENT_1_specificity.md, committed before this ran again): the original
        # criterion required top-k to beat bottom-k, which assumed bottom-k is inert. Measured, it
        # is not -- ablating five arbitrary heads at every position costs 11 nats against a 0.21
        # baseline. The comparator is the size-matched RANDOM null, which is what R1 exists to
        # supply and what I should have written the first time.
        rngc = random.Random(DRAW_SEED)
        hypc = set(top) | set(bot)
        poolc = [(L, h) for L in range(NL) for h in range(NH) if (L, h) not in hypc]
        nullc = np.array([run(rngc.sample(poolc, K)) - base for _ in range(N_DRAWS)])
        sdc = float(nullc.std(ddof=1))
        ok = d_top < 0 and (nullc.mean() - d_top) > 2 * sdc
        print(f"  null over {N_DRAWS} random draws: mean {nullc.mean():+.4f} sd {sdc:.4f} "
              f"range [{nullc.min():+.4f}, {nullc.max():+.4f}]")
        print(f"  top-{K} is {(nullc.mean()-d_top)/sdc:+.2f} sd BELOW the null mean")
        print(f"\n  ROUND-INVALIDATING CHECK: "
              f"{'PASS - top-k hurts induction and clears 2sd of the RANDOM null' if ok else 'FAIL'}")
        if not ok:
            print("  R2 has no known mechanism on this model: the selection score does not "
                  "identify heads whose removal hurts the outcome. Stop rather than proceed.")
        return 0 if ok else 2

    rng = random.Random(DRAW_SEED)
    hyp = set(top) | set(bot)
    pool = [(L, h) for L in range(NL) for h in range(NH) if (L, h) not in hyp]
    nulls = [run(rng.sample(pool, K)) - base for _ in range(N_DRAWS)]
    nv = np.array(nulls)
    sd = float(nv.std(ddof=1))

    res = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag, 'n_layers': NL, 'n_heads': NH, 'k': K, 'n_seq': N_SEQ, 'T': T,
           'dtype': args.dtype, 'ablate_positions': 'all',
           'baseline_logprob': base,
           'induction_top': [list(x) for x in top], 'induction_bottom': [list(x) for x in bot],
           'd_top': d_top, 'd_bottom': d_bot,
           'null': {'mean': float(nv.mean()), 'sd': sd, 'min': float(nv.min()),
                    'max': float(nv.max()), 'values': [float(x) for x in nv]},
           'top_pct_in_null': float((nv < d_top).mean() * 100),
           'sign_correct': bool(d_top < 0),
           'clears_2sd': bool(abs(d_top - nv.mean()) > 2 * sd),
           'floor_2sd_frac_of_baseline': float(2 * sd / abs(base)),
           # SD IS THE WRONG SUMMARY FOR THIS NULL AND THE DATA SAYS SO. On phi-3.5 one draw of 30
           # came in at -13.66 while the other 29 sat inside +-1.0; sd is 2.49 with it and 0.054
           # without -- a factor of 46. A mean/sd description of a heavy-tailed distribution is not
           # a description of it, so the percentile is reported alongside and is the one to prefer.
           'null_median': float(np.median(nv)),
           'null_p10': float(np.percentile(nv, 10)),
           'null_iqr': float(np.percentile(nv, 75) - np.percentile(nv, 25)),
           'n_outlier_draws': int(sum(abs(x) > 10 * (np.percentile(nv, 75) - np.percentile(nv, 25) or 1) for x in nv)),
           'clears_p10': bool(d_top < np.percentile(nv, 10)),
           # VALIDITY: a cell measures ablation of a mechanism only if the mechanism is THERE.
           # internlm2 scored baseline logprob -12.2, i.e. probability ~5e-6 on the correct token --
           # it does not do induction at all, so an ablation effect on it is an effect on nothing.
           'baseline_prob': float(np.exp(base)),
           'metric_measurable': bool(np.exp(base) > 0.1),
           'cell_valid': bool(np.exp(base) > 0.1)}

    print(f"\n  null over {N_DRAWS} size-matched draws: mean {nv.mean():+.4f} sd {sd:.4f} "
          f"range [{nv.min():+.4f}, {nv.max():+.4f}]")
    print(f"  top-{K} sits at the {res['top_pct_in_null']:.0f}th percentile of the null")
    print(f"  null median {res['null_median']:+.4f}  p10 {res['null_p10']:+.4f}  "
          f"IQR {res['null_iqr']:.4f}  outlier draws {res['n_outlier_draws']}")
    print(f"  SIGN {'CORRECT' if res['sign_correct'] else '*** INVERTED ***'} | "
          f"2sd: {'clears' if res['clears_2sd'] else 'DOES NOT CLEAR'} | "
          f"p10: {'clears' if res['clears_p10'] else 'does not clear'}")
    # Written as a plain variable rather than a multi-line f-string expression: PEP 701 allows the
    # latter from Python 3.12, the system interpreter here is 3.14 and accepted it, and the project
    # venv is 3.11 and did not. `ast.parse` under the wrong interpreter is not a syntax check.
    _v = "VALID" if res["cell_valid"] else (
        "INVALID (the mechanism is absent; an ablation effect here is an effect on nothing)")
    print(f"  baseline prob {res['baseline_prob']:.4f} -> cell {_v}")
    Path('results').mkdir(exist_ok=True)
    out = f"{args.out}_{args.tag}.json"
    json.dump(res, open(out, 'w'), indent=2, default=float)
    print(f"  -> {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
