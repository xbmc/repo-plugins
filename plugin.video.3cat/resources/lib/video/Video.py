import xbmc

from resources.lib.utils.Utils import parseDurada


class Video:

    def __init__(self, title, iconImage, thumbnailImage, information, url, durada,
                 fanart='', mediatype='video', show='', season=None, episode=None, aired=''):
        xbmc.log("plugin.video.3cat - video " + str(title) + ", " + str(url))
        self.title = title
        self.iconImage = iconImage or ''
        self.thumbnailImage = thumbnailImage or ''
        self.information = information or ''
        self.url = url
        self.durada = durada
        self.duration = parseDurada(durada)
        self.fanart = fanart or ''
        self.mediatype = mediatype
        self.show = show or ''
        self.season = season
        self.episode = episode
        self.aired = aired or ''
