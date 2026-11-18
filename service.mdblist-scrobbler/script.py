import os
import sys

_addon_root = os.path.dirname(os.path.abspath(__file__))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from resources.lib.script_entry import run

run()
