from builtins import object
import os


class Images(object):

    def __init__(self, addon_path):

        self.thumb_tv3 = os.path.join(addon_path, 'resources', 'media', 'tv3_thumbnail.png')
        self.thumb_324 = os.path.join(addon_path, 'resources', 'media', '324_thumbnail.png')
        self.thumb_c33 = os.path.join(addon_path, 'resources', 'media', 'c33_thumbnail.png')
        self.thumb_sx3 = os.path.join(addon_path, 'resources', 'media', 'sx3_thumbnail.jpeg')
        self.thumb_esp3 = os.path.join(addon_path, 'resources', 'media', 'esports3_thumbnail.png')
