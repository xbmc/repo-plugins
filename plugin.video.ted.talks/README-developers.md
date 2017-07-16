Run core tests (note some tests skipped at end) with:

`PYTHONPATH=$PYTHONPATH:$PWD/testSupport nosetests`

To run all tests. This may incur TED rate-limiting:

`PYTHONPATH=$PYTHONPATH:$PWD/testSupport EXCLUDE_RATE_LIMITED=false nosetests`
