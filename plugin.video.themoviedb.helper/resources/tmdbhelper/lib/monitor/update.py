from xbmc import Monitor
from tmdbhelper.lib.update.tagger import LibraryTagger


class UpdateMonitor(Monitor):
    """
    Monitors updating Kodi library
    """

    def onScanFinished(self, library):
        if library == 'video':
            LibraryTagger().run()
