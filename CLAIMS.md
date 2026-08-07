# Claim Register

This register defines the strongest claims this study may support. Claims not listed here
are not authorized, regardless of how the results look.

## Claim C0: the protocol transfers

**Statement.** The deficit-window protocol established for vision networks can be
instantiated for autoregressive language-model pretraining with an information-preserving
negative control, a seed-paired baseline, and an endpoint that separates unrepaired damage
from permanent damage.

**Evidence required.** A completed ladder in which every run shares one configuration apart
from its budget, the negative control's damage decays away, and the frozen decision code
returns a verdict without manual intervention.

**Maximum scope.** Methodological. The protocol is instantiable and its controls behave.

**Forbidden extension.** That the vision result replicates in language. C0 is about the
instrument, not the finding.

## Claim C1: onset-dependent permanent damage, or its absence

**Statement.** At this model scale and corpus, the gap left by a window-shuffle deficit
applied early in pretraining survives increases in the training budget, and survives them
more than the same deficit applied later — or it does not, at a stated resolution and up to
a stated top budget.

**Evidence required.** The full Section 5.4 conjunction of `preregistration.md`, including
a recovered negative control and a rejected primary permutation test in the registered
direction, with `Δ_primary` at or above the registered margin. For the negative form: a
non-rejecting primary test whose minimum detectable effect is at or below the margin.

**Maximum scope.** One architecture, one corpus, one budget, one deficit pair, one recovery
multiplier, one learning-rate schedule, single-digit seed counts.

**Forbidden extension.** Any statement about large language models, about production
pretraining, about data-curriculum policy, or about deficits other than the two registered
here. A result at 10M parameters is a result at 10M parameters.

**Named moderator.** Pawlak (arXiv:2510.09687) reports that critical-period effects can be
removed by a cyclic learning-rate schedule. This study uses warmup followed by cosine decay
and does not vary the schedule, so a positive result licenses "under this schedule" and
never "in language models". A negative result is correspondingly weaker, not stronger: an
absent effect under one schedule does not rule one out under another.

## Claim C2: the negative control bounds the interpretation

**Statement.** A scar under Deficit S is attributable to the destruction of order
information only because Deficit F — the same operation on the same tokens, differing only
in that its permutation is fixed and therefore invertible — does not scar.

**Evidence required.** The registered `fixed_early` ladder returns `TRANSIENT` or
`NO_EFFECT` — its gap decays to below the margin as the budget grows.

**Maximum scope.** Rules out the compute-loss explanation and the
any-early-perturbation-scars explanation, for these two deficits.

**Forbidden extension.** That all information-preserving perturbations are harmless, or that
Deficit F is a general-purpose control for other studies. A control that recovers has ruled
out one alternative, not the class — and the control this one replaced looked just as sound
in prose before pilot 2 measured it.

## Claim C3: a null here is a bounded null

**Statement.** If no onset effect is detected, the study establishes that any such effect is
smaller than the reported minimum detectable effect at this scale and budget.

**Evidence required.** A reported minimum detectable effect alongside the non-rejection, and
an explicit `calibrated null (underpowered)` label wherever that quantity exceeds the
registered margin.

**Maximum scope.** An upper bound on effect size under these conditions, at budgets up to
the top rung. `PERSISTENT` means survived this ladder; it never means permanent, and every
report of it carries the top budget it survived.

**Forbidden extension.** "Language models have no critical periods." Absence of evidence at
n=4 per cell is a resolution statement, not an existence statement.

**Relation to the existing null.** Constantinescu et al. (TACL 2024) found no critical
period for delayed second-language exposure. A null here would be a second null in a
different paradigm — degraded input during an early window rather than delayed exposure to
new material — which is worth reporting precisely because the paradigms are different. It
would not combine with theirs into a general claim, and the two nulls together still would
not cover the space.

## Explicit non-claims

This study cannot establish:

- anything about consciousness, subjective experience, self-modeling, or model welfare;
- anything about human language acquisition, child development, or biological critical
  periods, in either direction;
- that training-order effects in production-scale pretraining resemble these;
- that data curricula should or should not be ordered in any particular way;
- that "early training matters" as a general slogan — the registered claim is about one
  deficit pair under one recovery budget;
- that the representational (CKA) measures identify a mechanism; they are descriptive;
- that the TinyStories corpus is representative of natural language;
- that MLX, this hardware, or this implementation is free of common-mode error;
- that a gap surviving the top rung would survive a budget an order of magnitude larger.

## Provenance note

The idea for this study emerged from a philosophical conversation about development,
plasticity, and whether a frozen-weight model can be said to have grown. That lineage may
appear in a motivation section. It may not appear in a claim. The developmental framing
generated the hypothesis; it does not license any interpretation of the result, and a
reviewer who reads a developmental conclusion into these numbers is reading something this
register forbids.

## Claim transition rule

A completed study authorizes only a new, independently frozen preregistration — for a
larger scale, for additional deficits, or for an onset sweep. No result carries over
automatically, and no follow-up inherits this register.
