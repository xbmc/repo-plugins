import os
import sys

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from kofin.plugin.context import play_with_transcode

if __name__ == "__main__":
    play_with_transcode()
