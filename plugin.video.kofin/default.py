import os
import sys

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

# The gate first, and nothing of kofin's before it: a request it turns away
# must not have paid for the router's imports (plugin/gate.py).
from kofin.plugin import gate

_flight = gate.enter(sys.argv)
if _flight is not None:
    try:
        from kofin.plugin.router import dispatch

        dispatch(sys.argv)
    finally:
        gate.leave(_flight)
