"""Run the add-on's plugin entry point (Kodi calls it with the plugin URL in sys.argv)."""

import sys
import time


def main(started):
    """Handle one plugin call: play through the service if possible, else load the whole plugin.

    :param started: the time.time() at which Kodi started this call
    """
    from resources.lib.util import pluginbusy

    pluginbusy.begin()
    try:
        _run(started)
    finally:
        pluginbusy.end()


def _run(started):
    """Handle the call: see main."""
    # Through the service: much faster than loading the whole add-on for every channel switch.
    if "action=play" in sys.argv[2]:
        from resources.lib.service import quickplay

        if quickplay.run(sys.argv, started):
            return
    loading = time.time()
    from resources.lib import plugin

    plugin.run(sys.argv, started, imported=time.time() - loading)


main(time.time())
