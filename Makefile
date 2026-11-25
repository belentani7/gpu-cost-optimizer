# repo-forge:tareas
.PHONY: doctor test check all

doctor:
	python scripts/doctor.py

test:
	python -m pytest -q

check: doctor test

all: check
