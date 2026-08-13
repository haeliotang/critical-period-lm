PYTHON ?= python3
PYTHONPATH := src

REQUIRED_FILES := \
	README.md \
	STATUS.md \
	CLAIMS.md \
	preregistration.md

TRAIN_MB ?= 600
CALIBRATION_STEPS ?= 8000
LADDER_BASE ?= 2700
SEEDS ?= 0 1 2 3 4
REGISTERED_BASE ?= 1350

.PHONY: check compile test required-files-check rehearsal freeze freeze-check runs-check data calibrate ladder registered-ladder report report-calibration robustness

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

# The registered ladder: every condition at BASE, 2*BASE and 4*BASE. The endpoint is
# whether each condition's gap to baseline decays as the budget grows, so budget is the
# treatment and the rungs are not interchangeable with more seeds at one budget.
# Exploratory until the design is frozen: written to calibration/, excluded from results.
ladder:
	@for mult in 1 2 4; do \
		budget=$$(( $(LADDER_BASE) * $$mult )); \
		for s in $(SEEDS); do \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
				--condition baseline --seed $$s --total-steps $$budget || exit 1; \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
				--condition fixed_early_N4 --seed $$s --deficit fixed \
				--onset-frac 0.0 --duration-frac 0.16 --total-steps $$budget || exit 1; \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
				--condition shuffle_early_N4 --seed $$s --deficit shuffle \
				--onset-frac 0.0 --duration-frac 0.16 --total-steps $$budget || exit 1; \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train --calibration \
				--condition shuffle_late_N4 --seed $$s --deficit shuffle \
				--onset-frac 0.5 --duration-frac 0.16 --total-steps $$budget || exit 1; \
		done; \
	done
	$(MAKE) report-calibration

# The registered ladder. No --calibration: the trainer refuses to start unless the freeze
# verifies, and records land in runs/. Fresh seeds by Section 8.3 -- reusing the calibration
# seeds would make this a recomputation rather than a replication.
registered-ladder:
	@for mult in 1 2 4 8; do \
		budget=$$(( $(REGISTERED_BASE) * $$mult )); \
		for s in 10 11 12 13 14 15 16 17; do \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train \
				--condition baseline --seed $$s --total-steps $$budget || exit 1; \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train \
				--condition fixed_early_N4 --seed $$s --deficit fixed \
				--onset-frac 0.0 --duration-frac 0.16 --total-steps $$budget || exit 1; \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train \
				--condition shuffle_early_N4 --seed $$s --deficit shuffle \
				--onset-frac 0.0 --duration-frac 0.16 --total-steps $$budget || exit 1; \
			PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m critical_period_lm.train \
				--condition shuffle_late_N4 --seed $$s --deficit shuffle \
				--onset-frac 0.5 --duration-frac 0.16 --total-steps $$budget || exit 1; \
		done; \
	done
	$(MAKE) report

report:
	$(PYTHON) analysis/report.py

report-calibration:
	$(PYTHON) analysis/report.py --calibration

# Robustness exhibit, not a result. Enumerated after both registered verdicts were known;
# every artifact it writes says so. Writes to results/robustness/, never results/registered/.
robustness:
	$(PYTHON) analysis/multiverse.py v4
	$(PYTHON) analysis/multiverse.py v5

# Registered runs may not exist before the freeze tag does.
runs-check:
	@if test ! -f freeze-manifest.json; then \
		unexpected="$$(find runs -mindepth 2 -name run.json -print)"; \
		if test -n "$$unexpected"; then \
			echo "run artifacts exist but the design is not frozen:" >&2; \
			echo "$$unexpected" >&2; \
			exit 1; \
		fi; \
	fi
