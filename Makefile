PYTHON ?= python3
PYTHONPATH := src

REQUIRED_FILES := \
	README.md \
	STATUS.md \
	CLAIMS.md \
	preregistration.md

TRAIN_MB ?= 600
CALIBRATION_STEPS ?= 8000

.PHONY: check compile test required-files-check rehearsal freeze freeze-check runs-check data calibrate

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
