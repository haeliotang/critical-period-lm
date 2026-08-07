# Negative control replaced: vocabulary permutation to fixed window permutation

**Date:** 2026-08-06
**Design version:** v1.2-draft to v1.3-draft
**Decided:** after seeing the pilot 2 result, and because of it
**Pre-freeze:** yes. Nothing was frozen; no registered run exists.

## What changed

Deficit P (a fixed bijection over token ids, applied to inputs and targets for the deficit
window) is retired as the registered negative control. Deficit F replaces it: the same
window-reordering operation as Deficit S, with a single permutation drawn once for the study
and reused for every window, instead of resampled per window per batch.

## Why

The reasoning behind Deficit P was that a relabeled language is isomorphic to the original,
so a model trained under it learns a sound model of a renamed language and need only remap
its embedding layer on removal. Pilot 2 refuted this. At identical onset and duration:

| Condition | Delta vs baseline | Verdict |
| --- | --- | --- |
| `shuffle_early_N4` | +0.0027 | RECOVERED |
| `permute_early_N4` | +0.0324 | SCAR |

Twelve times the damage, from a manipulation that was supposed to be the harmless one, at a
matched onset and duration. With tied embeddings a vocabulary permutation invalidates the
whole input and output interface rather than perturbing the input; it is not the analogue of
a vertical flip. The prose argument was clean and the experiment disagreed with it.

Deficit F is a tighter match to what a negative control has to be: same operation, same
locus, same surface magnitude, differing only in whether the reordering is invertible.

## Status of this change

Untested. Deficit F is predicted to recover for the same kind of reason Deficit P was, and
that prediction has exactly the track record recorded above. Pilot 3 tests it. The claim in
`CLAIMS.md` C2 now says so explicitly.

## What was kept

The vocabulary-permutation code remains in `deficits.py` and stays under test, solely so
that pilots 1 and 2 remain reproducible from their archived records. It is not part of the
registered design.
