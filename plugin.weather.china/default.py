# -*- coding: utf-8 -*-
"""Single entry point for both plugin:// and weather-service invocations.

Kodi calls this file in two ways:
  * ``plugin://plugin.weather.china/?...``  -> interactive plugin menu
  * ``RunScript(plugin.weather.china,location1)`` or the weather extension
    point (every 30 min) -> weather provider; sys.argv[1] is 'locationN' / 'N'

Both xbmc.python.pluginsource and xbmc.python.weather point here, so whichever
extension Kodi resolves, the correct mode is selected by sys.argv[0].
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources"))

if __name__ == "__main__":
    if sys.argv and str(sys.argv[0]).startswith("plugin://"):
        from lib import ui
        ui.run()
    else:
        from lib import weatherprovider
        weatherprovider.run(sys.argv[1] if len(sys.argv) > 1 else "")
