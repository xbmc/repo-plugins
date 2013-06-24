#!/usr/bin/python
# -*- coding: utf-8 -*-

from converter import JsonListItemConverter 
from functools import wraps
from gagtv import GagTV, Keys, GagException
from xbmcswift2 import Plugin #@UnresolvedImport
import sys

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

PLUGIN_NAME = '9GAG TV'
PLUGIN_ID = 'plugin.video.9gagtv'
PLUGIN = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)
CONVERTER = JsonListItemConverter(PLUGIN)
GAGTV = GagTV()


@PLUGIN.route('/')
def createMainListing():
    items = [
        {
         'label': PLUGIN.get_string(10001),
         'path': PLUGIN.url_for(endpoint = 'createListOfTodaysVideos')
         },
         {
         'label': PLUGIN.get_string(10002),
         'path': PLUGIN.url_for(endpoint = 'createListOfArchives')
         }
    ]
    return items

@PLUGIN.route('/createListOfTodaysVideos/')
def createListOfTodaysVideos():
    videos = GAGTV.getTodaysVideos()
    return [CONVERTER.convertVideoToListItem(element)
            for element in videos]

@PLUGIN.route('/createListOfArchivedVideos/<pid>/')
def createListOfArchivedVideos(pid):
    videos = GAGTV.getArchivedVideos(pid)
    return [CONVERTER.convertVideoToListItem(element)
            for element in videos]

@PLUGIN.route('/createListOfArchives/')
def createListOfArchives():
    archives = GAGTV.getArchives()
    return [CONVERTER.convertArchiveToListItem(element)
            for element in archives]

@PLUGIN.route('/playVideo/<videoId>/')
def playVideo(videoId):
    url = 'plugin://plugin.video.youtube/?action=play_video&videoid=' + videoId
    PLUGIN.log.info('Playing url: %s' % url)
    return PLUGIN.set_resolved_url(url)

if __name__ == '__main__':
    PLUGIN.run()
