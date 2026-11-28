import xbmc


class FolderVideo:
    def __init__(self, name, url, mode, iconImage="", thumbnaiImage="", plot="", fanart=""):
        xbmc.log("plugin.video.3cat Creant folder video " + str(name) + ", " + str(url) + ", " + str(mode))
        self.name = name
        self.url = url
        self.mode = mode
        self.iconImage = iconImage or ''
        self.thumbnailImage = thumbnaiImage or ''
        self.plot = plot or ''
        self.fanart = fanart or ''
