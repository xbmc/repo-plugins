"""
SermonIndex for Kodi - entry point.

Kodi runs this file once per navigation step. All of the logic lives in
resources/lib/router.py (screens and routing) and resources/lib/api.py
(the SermonIndex API client).

    plugin://plugin.video.sermonindex/?action=speaker&slug=zac-poonen
"""

from resources.lib.router import run

if __name__ == "__main__":
    run()
