from builtins import object

import xbmc


class Video(object):

    def __init__(self, title, iconImage, thumbnailImage, information, url, durada):
        xbmc.log("plugin.video.3cat - video " + str(title) + ", " + str(url))
        self.title = title
        self.iconImage = iconImage
        self.thumbnailImage = thumbnailImage
        self.information = information
        self.url = url
        self.durada = durada

