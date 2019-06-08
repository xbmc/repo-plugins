#!/bin/sh
set -e
PYTHONPATH=$PYTHONPATH:$PWD/testSupport python2 -m "unittest" discover -s ./resources/lib/ -p "*_test.py"
