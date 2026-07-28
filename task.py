"""The synthetic binding task, vendored so every round runs from this repository alone.

`k` facts of the form *X owns the {obj}* and *the {obj} is in the {room} room*, then one question
whose answer is a room. Deliberately synthetic: these rounds are about the measurement apparatus,
and a task whose ground truth is generated leaves nothing to argue about in the answer key.
"""

PERSONS = ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank', 'Grace', 'Hank']
OBJECTS = ['pill', 'flag', 'mask', 'ball', 'coin', 'ring', 'wand', 'drum']

# The ORIGINAL room vocabulary. R1 replaced it after the readout detector found that phi-3.5-mini
# and internlm2 score two of these four on word FRAGMENTS — '▁p' for pine, 'f' for frost — so the
# logit being compared belonged to every word starting the same way. Kept here because the
# amendment that replaced it is part of the record, not a detail to be tidied away.
ROOMS = ['pine', 'gold', 'rust', 'frost']

# The shared vocabulary every cross-model round uses: whole single tokens under all four tokenizers
# tested. Chosen from 37 candidates that satisfied that constraint; no collision with OBJECTS.
ROOMS_SHARED = ['stone', 'iron', 'glass', 'water']
