#!/usr/bin/python

########################

import xbmcgui

from resources.lib.helper import *
from resources.lib.tmdb import *
from resources.lib.main import *

########################

class Main:
    def __init__(self):
        self.call = False
        self._parse_argv()

        if self.call == 'textviewer':
            textviewer(self.params)

        elif self.call == 'refresh_library_cache':
            get_local_media(force=True)

        else:
            ''' It takes a couple of milliseconds until the script starts (Kodi<->Python delay). This could cause double calls
                for users with a nervous "DO IT NOW!!!11!"-finger. This is a ugly but working workaround. Will be replaced with
                a better one if found and if it won't be too complex -> #TODO
            '''
            if not winprop('script.aeon.tajo.info-double_start_workaround.bool'):
                winprop('script.aeon.tajo.info-double_start_workaround.bool', True)
                execute('AlarmClock(ClearWorkaroundProp,ClearProperty(script.aeon.tajo.info-double_start_workaround,home),00:01,silent)')
                self.run()

    def run(self):
        if self.call:
            TheMovieDB(self.call, self.params)

        else:
            call = DIALOG.select(ADDON.getLocalizedString(32005), [ADDON.getLocalizedString(32004), xbmc.getLocalizedString(20338), xbmc.getLocalizedString(20364)])
            if call == 0:
                call = 'person'
            elif call == 1:
                call = 'movie'
            elif call == 2:
                call = 'tv'
            else:
                quit()

            query = DIALOG.input(xbmc.getLocalizedString(19133), type=xbmcgui.INPUT_ALPHANUM)
            TheMovieDB(call, {'query': query})

    def _parse_argv(self):
        args = sys.argv

        for arg in args:
            if arg == ADDON_ID:
                continue
            if arg.startswith('call='):
                self.call = arg[5:].lower()
            else:
                try:
                    self.params[arg.split("=")[0].lower()] = "=".join(arg.split("=")[1:]).strip()
                except Exception:
                    self.params = {}


if __name__ == "__main__":
    Main()
