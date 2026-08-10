# Claim Register

This register defines the strongest claims this study may support. Claims not listed here
are not authorized, regardless of how the results look.

## Claim C0: the protocol transfers

**Statement.** The deficit-window protocol established for vision networks can be
instantiated for autoregressive language-model pretraining with an information-preserving
negative control, a seed-paired baseline, and an endpoint that estimates how fast damage
decays rather than scoring its level at one budget.

**Evidence required.** A completed ladder in which every run shares one configuration apart
from its budget, every deficit seed has a baseline partner, the control's exponent is
fitted, and the frozen decision code returns a verdict without manual intervention.

**Maximum scope.** Methodological. The protocol is instantiable and its controls behave.

**Forbidden extension.** That the vision result replicates in language. C0 is about the
instrument, not the finding.

## Claim C1: onset-dependent permanent damage, or its absence

**Statement.** At this model scale and corpus, damage from a window-shuffle deficit applied
early in pretraining is repaired more slowly than the same deficit applied later — or it is
not, at a stated resolution and over a stated budget range.

The claim is **comparative**. It is a difference of decay exponents and carries no statement
about whether either damage is permanent.

**Evidence required.** The Section 5.7 conjunction of `preregistration.md`: a usable
control, a rejected one-sided permutation test in the critical-period direction, and an
exponent difference at or above the registered margin. For the negative form: a
non-rejecting two-sided test with the difference below the margin.

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

**Statement.** A difference in repair rate under Deficit S is attributable to the
destruction of order information only because Deficit F — the same operation on the same
tokens, differing only in that its permutation is fixed and therefore invertible — is the
reference it is measured against.

**Evidence required.** A fitted control exponent with at least two seeds and damage above
the level floor. The control is the anchor, not a hypothesis: its own exponent absorbs
whatever the measurement does to every condition alike — the baseline curve's shape above
all — so a difference from it is a difference in the deficit.

**A control far from `alpha = 1` is not a failure.** Design v3 gated on that and was wrong;
ladder 2 failed a perfectly serviceable control because the theoretical anchor assumed a
constant learning-curve slope that the same data showed falling 30% per doubling.

**Maximum scope.** Rules out the compute-loss explanation and the
any-early-perturbation-scars explanation, for these two deficits.

**Forbidden extension.** That all information-preserving perturbations are harmless, or that
Deficit F is a general-purpose control for other studies. A control that recovers has ruled
out one alternative, not the class — and the control this one replaced looked just as sound
in prose before pilot 2 measured it.

## Claim C3: a null here is a bounded null

**Statement.** If no onset effect is detected, the study establishes that any such effect is
smaller than the reported minimum detectable effect at this scale and budget.

**Evidence required.** The non-rejecting two-sided test reported together with the exponent
margin it was weighed against, and with the per-seed exponents that produced it.

**Maximum scope.** An upper bound on the exponent difference under these conditions, over
the budget range the ladder spans. An exponent is fitted on three rungs; it describes decay
within that range and is an extrapolation outside it.

**Forbidden extension.** "Language models have no critical periods." Absence of evidence at
five seeds per arm is a resolution statement, not an existence statement.

**Relation to the existing null.** Constantinescu et al. (TACL 2024) found no critical
period for delayed second-language exposure. A null here would be a second null in a
different paradigm — degraded input during an early window rather than delayed exposure to
new material — which is worth reporting precisely because the paradigms are different. It
would not combine with theirs into a general claim, and the two nulls together still would
not cover the space.

## Claim C4: a reverse onset effect, if found, is a finding and not a critical period

**Statement.** If late damage decays measurably more slowly than early damage, onset matters
in the direction opposite to every critical-period account.

**Evidence required.** A rejected two-sided permutation test with the exponent difference at
or above the registered margin, against a fitted control.

**Maximum scope.** A description of these two onsets at this scale. The mechanism is not
identified and no mechanism is claimed.

**Forbidden extension.** That late training is more fragile than early training in general,
or that this reverses the vision literature. It is one contrast, at one scale, under one
schedule.

**Provenance, stated plainly.** This verdict was added to the register *after* ladder 1
pointed at the pattern. The exploratory data motivated giving it a name; it did not supply
evidence for it, and the registered study is what would. Without a name for it the design
would have absorbed the most interesting thing in its own data into a null, which is the
failure this register exists to prevent — but the ordering is recorded so a reader can
discount it as they see fit.

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
- that a gap surviving the top rung would survive a budget an order of magnitude larger;
- that the fitted power law holds outside the budget range the ladder spans;
- that `alpha = 1` proves a pure lag rather than failing to distinguish one;
- **whether any damage measured here is a lag or a permanent scar.** That is an absolute
  question, it needs `Δ_eff` estimated across rungs, and three rungs cannot pin it down.
  Section 3.2.1 drops it rather than answering it, and no exponent reported here may be
  pressed into service for it.

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
