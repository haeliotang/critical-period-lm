# A frozen claim's statement sentence is wider than its own forbidden extension

**Date:** 2026-08-16
**Design versions affected:** none — no design element changes and no verdict changes
**Status of the study:** both registered ladders complete, verdicts final, write-up in draft.
**What this entry is:** a record that the frozen register contains a tension, which of the two
readings governs, and why the frozen file is not being edited to remove it.

## What was found

`CLAIMS.md` C4 opens with:

> **Statement.** If late damage decays measurably more slowly than early damage, onset matters
> in the direction opposite to every critical-period account.

Four paragraphs later the same claim says:

> **Forbidden extension.** That late training is more fragile than early training in general,
> **or that this reverses the vision literature.** It is one contrast, at one scale, under one
> schedule.

The statement asserts what the forbidden extension prohibits. Both were written before any
registered data existed.

## Why the statement is the wrong half

Checked against the source while assembling the paper's reference list. Achille, Rovere and
Soatto (ICLR 2019, §2) slide a fixed-length deficit window across onsets and report verbatim:

> we observe that the sensitivity to the deficit peaks in the central part of the early rapid
> learning phase (at around 30 epochs), while introducing the deficit later produces little or
> no effect.

**Their onset curve is non-monotonic and its peak is not at the start of training.** A deficit
at onset zero is not the most damaging case in the seminal result either. "Opposite to every
critical-period account" therefore describes no account that exists.

Two further reasons the comparison is unavailable at all:

1. **Two onsets cannot recover a shape.** Placing our onsets on their curve would need a
   normalisation between a 300-epoch CIFAR schedule and a 1,350–10,800 step ladder. None is
   established, and with two points there is nothing to place.
2. **The endpoints differ.** Their sensitivity is a level at a fixed training length. This
   study's own Section 1.1 argues that a level at one training length cannot separate damage
   that is permanent from damage that is behind. A result cannot contradict a measurement it
   simultaneously argues is not measuring the thing.

## What changes

Nothing in the design, the records, the frozen code or the verdict. `REVERSE_ONSET_EFFECT` is
the name the frozen decision code gives a measured relation between two exponents; it is
defined by the registered contrast and not by any relation to prior literature.

The mutable prose that asserted the unguarded form is corrected: `README.md` and
`paper/draft.md`. The paper gains a Section 5 passage stating the above, a Section 4 entry
declaring the shape of the onset curve unidentified, and a limitation recording that onset and
learning-rate position are confounded by construction in this design.

## What is deliberately not done

`CLAIMS.md` is not edited. It is in the freeze corpus, the tension is between two sentences
that were both registered in advance, and the narrower one already governs — a forbidden
extension is not advisory. Editing the statement now would be revising a registered claim
after seeing which half the evidence favoured, which is the exact move the register exists to
prevent. **The guard rail worked; a register whose prose is edited whenever it chafes is not a
register.**

## Provenance of the catch

Found by checking a citation, not by a reviewer and not by the data. The draft's related-work
section had carried the claim through every revision without anyone reading the cited
experiment closely enough to notice that its own onset curve refutes the gloss.
