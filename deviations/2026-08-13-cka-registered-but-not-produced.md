# A registered secondary measure was not produced: layerwise CKA

**Date:** 2026-08-13
**Design versions affected:** v1 through v5 (the measure survived every revision unchanged)
**Status of the study:** both registered ladders complete; this entry is written before the
write-up, not after a reviewer asked.

## What was registered

`preregistration.md` §5.8 lists among the secondary measures:

> Layerwise CKA between each deficit run and its seed-matched baseline at the top rung.

Kornblith et al. (arXiv:1905.00414) is cited in §2 as its source.

## What was produced

Nothing. There is no CKA implementation in `src/`, `analysis/` or `tests/`, and none was
ever written.

## Why it cannot now be produced from the existing evidence

CKA needs activations, which need weights. **The run records contain no checkpoints.** A run
directory holds exactly one file, `run.json`, whose fields are the config, the config hash,
the deficit schedule, the loss curves, the final held-out loss, throughput and the data
manifest. `.gitignore` excludes `checkpoints/`, and the trainer never wrote any.

Producing CKA would therefore require re-running all 188 registered runs with checkpointing
added. That is a new study, not an analysis of this one.

## Why this does not affect any verdict

§5.8 states that secondary measures are "descriptive only; none can promote, demote or
qualify a primary verdict", and `CLAIMS.md` lists among the non-claims "that the
representational (CKA) measures identify a mechanism; they are descriptive". Both registered
verdicts — v4 `INCONCLUSIVE` and v5 `REVERSE_ONSET_EFFECT` — rest entirely on held-out loss
and are unchanged.

## Why it is recorded rather than quietly dropped

A registered measure that goes unreported is indistinguishable, from the outside, from one
that was computed and disliked. The entry exists so that a reader can tell which of those
happened here. **It was never computed.**

## Consequence for the write-up

The mechanism behind the effect is not identified, and CKA was the one registered measure
that might have said anything about representation. Its absence is part of why
`CLAIMS.md` C4 forbids any mechanistic reading. The write-up must state that no
representational measure was taken, rather than leaving the §5.8 list to imply one was.

## If there is a follow-up

Checkpointing at the top rung costs about 30 MB per run and no training time. Any successor
design should save it, and should treat this entry as the reason.

## Postscript: an attempted edit to the frozen text, and its reversal

On writing this entry the frozen `preregistration.md` §5.8 was also edited, to strike through
the CKA line and point here. `make freeze-check` rejected it immediately:

    FREEZE VIOLATION: preregistration.md changed after freeze

The edit was wrong and has been reverted. §10 of the preregistration says amendments after
the freeze are new files under `deviations/`, and the frozen text is never edited — which is
exactly what this file is. Annotating the registered document to record that one of its
measures went unproduced is still annotating the registered document, and a reader who wants
to know what was registered must be able to read it as it stood.

Recorded because the mechanism catching its author is the only evidence that it catches
anyone.
