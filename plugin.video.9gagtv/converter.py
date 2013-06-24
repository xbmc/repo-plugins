#!/usr/bin/python
# -*- coding: utf-8 -*-
from gagtv import GagTV, Keys, GagException

class JsonListItemConverter(object):

    def __init__(self, PLUGIN):
        self.plugin = PLUGIN

    def convertVideoToListItem(self, video):
        name = video[Keys.TITLE].encode('utf-8')
        image = video[Keys.THUMBNAIL].encode('utf-8')
        vid = video[Keys.YOUTUBE_VIDEO_ID].encode('utf-8')
        return {
                'label': name,
                'path': self.plugin.url_for('playVideo', videoId = vid),
                'icon' : image,
                'is_playable': True,
                }

    def convertArchiveToListItem(self, archive):
        name = archive[Keys.TITLE].encode('utf-8')
        playlistId = archive[Keys.PLAYLIST_ID].encode('utf-8')
        return {
                'label': name,
                'path': self.plugin.url_for('createListOfArchivedVideos', pid = playlistId),
                }
