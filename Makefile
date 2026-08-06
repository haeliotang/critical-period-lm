PYTHON ?= python3
PYTHONPATH := src

REQUIRED_FILES := \
	README.md \
	STATUS.md \
	CLAIMS.md \
	preregistration.md

TRAIN_MB ?= 600
CALIBRATION_STEPS ?= 8000
PILOT_STEPS ?= 5400

.PHONY: check compile test required-files-check rehearsal freeze freeze-check runs-check data calibrate pilot report report-calibration

# Everything that must pass before the design may be frozen.
check: compile required-files-check test freeze-check runs-check

compile:
	$(PYTHON) -m compileall -q src tests

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests

required-files-check:
	@for path in $(REQUIRED_FILES); do \
		test -f "$$path" || { echo "missing required file: $$path" >&2; exit 1; }; \
	done

# The rehearsal gate on its own: the decision rules against planted ground truths.
rehearsal:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest tests.test_decision_rules -v

# Write the manifest. Run once, after `make check` passes, then tag it.
freeze:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.freeze build

# Before the freeze this reports "not frozen" and passes; after it, any drift fails.
freeze-check:
	@if test -f freeze-manifest.json; then \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.freeze verify; \
	else \
		echo "design not frozen yet: no freeze-manifest.json"; \
	fi

# Download TinyStories, fit the tokenizer, encode. Writes data/manifest.json, whose
# digests are folded into every run's config hash.
data:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.data prepare --train-mb $(TRAIN_MB)

# Exploratory. Written to calibration/, excluded from every analysis, exempt from the
# freeze gate. Use it to measure throughput and find the budget at which loss plateaus.
calibrate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train \
		--calibration --condition calibration --total-steps $(CALIBRATION_STEPS)

# A scaled-down rehearsal of the primary contrast, at PILOT_STEPS instead of the full
# budget. Answers four questions at once: baseline seed variance (which sets the margin and
# therefore all of the study's power), whether Deficit S hurts, whether Deficit P recovers,
# and whether the analysis path works on real records rather than synthetic ones.
# Exploratory throughout: written to calibration/, excluded from every registered analysis.
pilot:
	@for s in 0 1 2 3 4; do \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
			--condition baseline --seed $$s --total-steps $(PILOT_STEPS) || exit 1; \
	done
	@for s in 0 1 2; do \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
			--condition shuffle_early_N4 --seed $$s --deficit shuffle \
			--onset-frac 0.0 --duration-frac 0.16 --total-steps $(PILOT_STEPS) || exit 1; \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
			--condition shuffle_late_N4 --seed $$s --deficit shuffle \
			--onset-frac 0.5 --duration-frac 0.16 --total-steps $(PILOT_STEPS) || exit 1; \
		PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
			--condition permute_early_N4 --seed $$s --deficit permute \
			--onset-frac 0.0 --duration-frac 0.16 --total-steps $(PILOT_STEPS) || exit 1; \
	done
	$(MAKE) report-calibration

report:
	$(PYTHON) analysis/report.py

report-calibration:
	$(PYTHON) analysis/report.py --calibration

# Registered runs may not exist before the freeze tag does.
runs-check:
	@if test ! -f freeze-manifest.json; then \
		unexpected="$$(find runs -mindepth 1 ! -name README.md -print)"; \
		if test -n "$$unexpected"; then \
			echo "run artifacts exist but the design is not frozen:" >&2; \
			echo "$$unexpected" >&2; \
			exit 1; \
		fi; \
	fi
