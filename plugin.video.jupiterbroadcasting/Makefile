# Makefile

default: venv

.PHONY: tests


venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	venv/bin/pip install -Ur requirements.txt
	venv/bin/pip install -Ur tests/requirements.txt
	touch venv/bin/activate

tests:
	python -m unittest discover
