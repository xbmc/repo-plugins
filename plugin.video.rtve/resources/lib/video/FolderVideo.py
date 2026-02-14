from builtins import object
import xbmc

class FolderVideo(object):
    def __init__(self, name, url, mode, iconImage ="", thumbnaiImage=""):
        """

        :rtype: object
        """
        xbmc.log("plugin.video.rtve Creant folder video " + str(name) + ", " + str(url) + ", " + str(mode), xbmc.LOGDEBUG)
        self.name = name
        self.url = url
        self.mode = mode
        self.iconImage = iconImage
        self.thumbnailImage = thumbnaiImage



