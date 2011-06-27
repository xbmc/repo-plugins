import sys
import os.path
import xbmcaddon

addon = xbmcaddon.Addon("plugin.program.mavi");
ROOT = addon.getAddonInfo("path") + os.sep
sys.path.insert(0, ROOT + "src")

from mavi import Program

DEBUGING = False 

# append pydev remote debugger
if DEBUGING:
    # Make pydev debugger works for auto reload.
    try:
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to remote console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " +
            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        sys.exit(1)

# start app
Program(sys.argv)