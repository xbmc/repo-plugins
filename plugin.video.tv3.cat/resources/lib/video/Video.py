from builtins import object
class Video(object):

    def __init__(self, title, iconImage, thumbnailImage, information, url, durada):

        self.title = title
        self.iconImage = iconImage
        self.thumbnailImage = thumbnailImage
        self.information = information
        self.url = url
        self.durada = durada

