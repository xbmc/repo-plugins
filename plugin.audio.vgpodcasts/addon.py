# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Espen Hovlandsdal

import xbmcplugin
import podcastapi
from xbmcplugin import addDirectoryItem
from xbmcplugin import endOfDirectory
from xbmcgui import ListItem
import routing

plugin = routing.Plugin()

@plugin.route('/')
def root():
    xbmcplugin.setContent(plugin.handle, 'albums')
    shows = podcastapi.shows()
    urls = [plugin.url_for(list_episodes, slug=show.id) for show in shows]
    view(shows, urls=urls)

@plugin.route('/show/<slug>')
def list_episodes(slug):
    xbmcplugin.setContent(plugin.handle, 'songs')
    episodes = podcastapi.episodes(slug)
    urls = [item.media_url for item in episodes]
    view(episodes, urls=urls)

def view(items, update_listing=False, urls=None):
    total = len(items)
    for item, url in zip(items, urls):
        is_episode = isinstance(item, podcastapi.Episode)

        title = getattr(item, 'title')
        info = { 'title': title }

        li = ListItem(title)
        li.setLabel2(item.subtitle)
        li.setIconImage(item.thumb or '')
        li.setArt({ 'thumb': item.logo or '' })

        if is_episode:
            li.setProperty('mimetype', 'audio/mpeg')
            li.setProperty('isplayable', 'true')
            li.addStreamInfo('audio', { 'codec': 'mp3', 'channels': 2 })

            info['duration'] = item.duration
            info['year'] = item.year

        li.setInfo('music', info)
        addDirectoryItem(plugin.handle, url, li, not is_episode, total)

    endOfDirectory(plugin.handle, updateListing=update_listing)

if __name__ == '__main__':
    plugin.run()
