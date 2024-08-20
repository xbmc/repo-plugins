import xbmc


class UpdateMonitor(xbmc.Monitor):
    """
    Monitors updating Kodi library
    """

    @staticmethod
    def run_library_tagger():
        from threading import Thread
        from tmdbhelper.lib.update.tagger import LibraryTagger
        Thread(target=LibraryTagger).start()

    def onScanFinished(self, library):
        if library == 'video':
            self.run_library_tagger()
