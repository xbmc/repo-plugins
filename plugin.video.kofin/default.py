import os
import sys

import xbmc

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

# The gate first, and nothing of kofin's before it: a request it turns away
# must not have paid for the router's imports (plugin/gate.py).
from kofin.plugin import gate

# A play's stop check next, still ahead of the router's imports: Kodi raises a
# stop only on the Monitors alive when it stops the script
# (XBPython::NotifyScriptAborting), and a viewer can cancel the busy dialog
# while those imports run (0.8 s of them on a Pi 3 just after the add-on was
# reloaded). A play only (gate.plays): a Monitor nobody waits on costs every
# Python thread in Kodi a step per announcement while it lives.
_STOP = xbmc.Monitor().abortRequested if gate.plays(sys.argv) else None

_flight = gate.enter(sys.argv)
if _flight is not None:
    try:
        from kofin.plugin.router import dispatch

        dispatch(sys.argv, stop=_STOP)
    finally:
        # A reused interpreter parks with this module's globals, and a Monitor
        # kept in one collects a callback per announcement until the next
        # script runs; the Request that also held the check died with the call.
        _STOP = None
        gate.leave(_flight)
