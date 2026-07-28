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

## selftest + headline, and a non-zero exit if any README number is stale
verify: selftest
	@$(PY) headline.py --check
