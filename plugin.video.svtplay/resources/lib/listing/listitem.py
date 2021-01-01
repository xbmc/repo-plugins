# -*- coding: utf-8 -*-
from __future__ import absolute_import,unicode_literals


class PlayItem(object):
    """
    A generic SVT Play list item
    """
    VIDEO_ITEM = "video"
    SHOW_ITEM = "show"

    def __init__(self, title, id, item_type, thumbnail="", geo_restricted=False, info={}, fanart=""):
        if not title:
            raise ValueError("Title is missing!")
        if not id:
            raise ValueError("ID is missing!")
        if not item_type:
            raise ValueError("Item type missing!")
        self.title = title
        self.id = id
        self.thumbnail = thumbnail
        self.geo_restricted = geo_restricted
        self.item_type = item_type
        self.info = info
        self.fanart = fanart

    def __str__(self):
        return "{title:" + self.title + ", id:" + self.id + "}"

    def __repr__(self):
        return self.__str__()

class VideoItem(PlayItem):
    """
    A video list item.
    """
    def __init__(self, title, video_id, thumbnail, geo_restricted, info={}, fanart="", season_title=""):
        self.season_title = season_title
        super(VideoItem, self).__init__(title, video_id, PlayItem.VIDEO_ITEM, thumbnail, geo_restricted, info, fanart)

class ShowItem(PlayItem):
    """
    A show list item, which means a folder containing VideoItems
    """
    def __init__(self, title, show_id, thumbnail, geo_restricted, info={}, fanart=""):
        super(ShowItem, self).__init__(title, show_id, PlayItem.SHOW_ITEM, thumbnail, geo_restricted, info, fanart)