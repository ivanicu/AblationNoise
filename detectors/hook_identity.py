#!/usr/bin/env python3
"""DETECTOR 9 — does the ablation hook remove the head it says it removes?

TEN ROUNDS REST ON ONE UNVERIFIED ASSUMPTION: that zeroing `x[0, -1, h*HD:(h+1)*HD]` on the input
of a layer's output projection removes exactly head h's contribution. That requires the heads to be
concatenated in that order, in that slice, in the tensor that projection receives -- an
architecture fact, never checked, on four model families with three different module names
(`self_attn.o_proj`, `attention.wo`) and at least one fused QKV.

THE IDENTITY IS EXACT AND NEEDS NO STATISTICS. Ablating head h must change the projection's OUTPUT
by exactly

    -W_O[:, h*HD:(h+1)*HD] @ x[h*HD:(h+1)*HD]

to machine precision. Anything else means the slice is not that head -- and every number in this
repository would be about a mislabelled object. It checks the ADDRESS and the BOUNDARIES at once.

    python3 detectors/hook_identity.py --model <hf-path> --tag <name> [--layer L]
"""
from __future__ import annotations
import argparse, json, torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
_HERE_F = __import__("pathlib").Path(__file__).resolve()
# A BASENAME DOES NOT IDENTIFY A FILE. `_PRODUCER = Path(__file__).name` recorded "run.py", which
# eleven rounds share, so the provenance check looked it up with a glob, took whichever came first,
# and reported that it had NOT guessed. It convicted R11's result against R6's runner. The earlier
# fix -- "read the producer from the file, do not infer it from the directory" -- was right and
# incomplete: what the file recorded could not name the object either.
_ROOT_F = next(p for p in _HERE_F.parents if (p / "Makefile").exists())
_PRODUCER = str(_HERE_F.relative_to(_ROOT_F))
_CODE_VERSION = __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()[:8]
PROMPT = ("Alice owns the pill. The pill is in the pine room.\n"
          "Question: Which room should Alice go to find their object?\nAnswer: The")


def resolve(layer):
    for an in ('self_attn', 'attention', 'attn', 'self_attention'):
        a = getattr(layer, an, None)
        if a is None:
            continue
        for pn in ('o_proj', 'wo', 'out_proj', 'dense', 'proj'):
            p = getattr(a, pn, None)
            if p is not None:
                return f'{an}.{pn}', p
    return None, None


@torch.no_grad()
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--layer', type=int, default=None)
    ap.add_argument('--tol', type=float, default=1e-4)
    # THE DEVICE WAS HARDCODED TO CPU AND THE QUEUE LABEL SAID GPU. internlm2 was submitted to the
    # GPU queue to escape a CPU-only NaN, and ran on the CPU anyway because this file said so. The
    # label and the operation disagreed one layer up from the code -- in the job description.
    ap.add_argument('--device', default='cpu', choices=['cpu', 'cuda'])
    ap.add_argument('--out', default=str(HERE.parent / 'R1_noise_floor' / 'results'
                                         / 'hook_identity'))
    args = ap.parse_args()
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(args.model, trust_remote_code=True,
                                             torch_dtype=torch.float32, device_map=args.device,
                                             attn_implementation='eager').eval()
    m.config.use_cache = False
    NL, NH = m.config.num_hidden_layers, m.config.num_attention_heads
    HD = m.config.hidden_size // NH
    L = args.layer if args.layer is not None else NL // 2 + (NL - NL // 2) // 2
    name, proj = resolve(m.model.layers[L])
    if proj is None:
        raise SystemExit(f"REFUSED: no output projection found on {args.tag} layer {L}")
    enc = {k: v.to(args.device) for k, v in tok(PROMPT, return_tensors='pt').items()}

    cap, out = {}, {}
    h1 = proj.register_forward_pre_hook(lambda mod, a: cap.__setitem__('x', a[0].detach().clone()))
    h2 = proj.register_forward_hook(lambda mod, a, o: out.__setitem__('y', o.detach().clone()))
    logits = m(**enc).logits
    h1.remove(); h2.remove()
    x0, y0, WO = cap['x'][0, -1].clone(), out['y'][0, -1].clone(), proj.weight.data

    # POSITIVE CONTROL FOR THIS INSTRUMENT, AND IT WAS MISSING ON THE FIRST RUN. The unablated
    # forward must be finite before any identity is worth computing. internlm2-chat-1.8b's
    # vendored modeling code produces an ALL-NaN forward on CPU with eager attention -- weights
    # finite, activations NaN -- and the first version of this file reported that as
    # HOOK-MISLABELLED. That is UNVERIFIED folded into OVERTURNED, this repository's cardinal
    # sin, committed by a detector on its second invocation. The model runs correctly on GPU;
    # the statement is about the CPU path, not about the hook.
    for nm, tsr in (('logits', logits), ('projection input', x0), ('projection output', y0),
                    ('W_O', WO)):
        if not torch.isfinite(tsr).all():
            bad = int((~torch.isfinite(tsr)).sum())
            res = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag, 'layer': L, 'module': name,
                   'verdict': 'UNRUNNABLE',
                   'why': f"the UNABLATED forward is not finite: {bad} non-finite values in "
                          f"{nm}. Nothing about the hook can be concluded from this run."}
            pth = f"{args.out}_{args.tag}.json"
            Path(pth).parent.mkdir(parents=True, exist_ok=True)
            json.dump(res, open(pth, 'w'), indent=2)
            print(f"  {args.tag}  layer {L} at .{name}")
            print(f"  UNRUNNABLE: {res['why']}")
            print(f"  -> {pth}")
            return 0

    active, errs = {'h': 0}, []
    for h in range(NH):
        active['h'] = h

        def pre(mod, a):
            z = a[0].clone()
            z[0, -1, active['h'] * HD:(active['h'] + 1) * HD] = 0
            return (z,) + a[1:]

        o2 = {}
        a1 = proj.register_forward_pre_hook(pre)
        a2 = proj.register_forward_hook(lambda mod, a, o: o2.__setitem__('y', o.detach().clone()))
        m(**enc)
        a1.remove(); a2.remove()
        exp = -(WO[:, h * HD:(h + 1) * HD] @ x0[h * HD:(h + 1) * HD])
        got = o2['y'][0, -1] - y0
        errs.append((got - exp).norm().item() / max(1e-12, exp.norm().item()))

    import math
    if any(math.isnan(e) for e in errs):
        n_nan = sum(math.isnan(e) for e in errs)
        res = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag, 'layer': L, 'module': name,
               'verdict': 'UNRUNNABLE', 'per_head_rel_err': errs,
               'why': f"{n_nan} of {len(errs)} heads produced a NaN relative error. NaN is not a "
                      f"large error; it is no measurement. UNVERIFIED, not MISLABELLED."}
        pth = f"{args.out}_{args.tag}.json"
        Path(pth).parent.mkdir(parents=True, exist_ok=True)
        json.dump(res, open(pth, 'w'), indent=2)
        print(f"  {args.tag}  layer {L} at .{name}\n  UNRUNNABLE: {res['why']}\n  -> {pth}")
        return 0
    worst = max(errs)
    ok = worst < args.tol
    print(f"  {args.tag}  layer {L} at .{name}  NH={NH} HD={HD}  W_O {tuple(WO.shape)}")
    print(f"  worst relative error over {NH} heads: {worst:.2e}  (tolerance {args.tol:g})")
    print(f"  -> {'HOOK ADDRESSES THE RIGHT SLICE' if ok else '*** HOOK IS MISLABELLED ***'}")
    res = {'code_version': _CODE_VERSION, 'producer': _PRODUCER, 'model': args.tag, 'layer': L,
           'module': name, 'device': args.device, 'n_heads': NH, 'head_dim': HD, 'worst_rel_err': worst, 'per_head_rel_err': errs,
           'tolerance': args.tol, 'verdict': 'HOOK-CORRECT' if ok else 'HOOK-MISLABELLED'}
    p = f"{args.out}_{args.tag}.json"
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(p, 'w'), indent=2)
    print(f"  -> {p}")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
