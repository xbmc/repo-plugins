import os
import sys

_addon_root = os.path.dirname(os.path.abspath(__file__))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from resources.lib.watchlist_plugin import run

if __name__ == "__main__":
    run()
