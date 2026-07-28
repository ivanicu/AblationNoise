# The handle: what a stranger runs before deciding whether to read anything.
#
# `make headline` needs no GPU, no model download and no network. It reads the checked-in result
# files and prints the numbers the README claims -- so the claim and the artifact cannot drift
# apart silently, which is the failure this whole repository is about.

PY ?= python3

.PHONY: headline selftest verify all

all: selftest headline

## the numbers in the README, recomputed from the checked-in results
headline:
	@$(PY) headline.py

## every detector replays the real incident that produced it
selftest:
	@$(PY) detectors/readout_tokens.py  --selftest
	@$(PY) detectors/circularity.py     --selftest
	@$(PY) detectors/control_fitness.py --selftest
	@$(PY) detectors/prose_numbers.py   --selftest
	@$(PY) detectors/arm_contrast.py    --selftest
	@$(PY) detectors/attack_detectors.py

## verify the ablation hook removes the head it names (needs torch; not part of `verify`)
hook:
	@$(PY) detectors/hook_identity.py --model $(MODEL) --tag $(TAG)

## selftest + headline, and a non-zero exit if any README number is stale.
## STANDARD LIBRARY ONLY -- no numpy, no torch, no network. Checked by cloning the repo and
## running this with a stock interpreter, because a verification path that needs a scientific
## stack is not a path a reader will take.
verify: selftest
	@$(PY) validate_defects.py
	@$(PY) validate_provenance.py
	@$(PY) headline.py --check
	@$(PY) detectors/prose_numbers.py

## R4's re-analysis of R1's results. Needs numpy; regenerates R4_predictability/results/.
## Everything above reads the checked-in output of this, so `verify` does not depend on it.
r4:
	@$(PY) R4_predictability/run.py --check
