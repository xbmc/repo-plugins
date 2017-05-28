# Makefile

default: venv

venv-arch:

venv: venv/bin/activate
venv-arch: venv/bin/activate-arch

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	venv/bin/pip install -Ur requirements.txt
	touch venv/bin/activate

venv/bin/activate-arch: requirements.txt
	test -d venv || virtualenv2 venv
	venv/bin/pip2 install -Ur requirements.txt
	touch venv/bin/activate

tests-arch:
	python2 -m unittest discover

tests:
	python -m unittest discover
