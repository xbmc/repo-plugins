# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin

class Items:

    def __init__(self, plugin):
        self.cache = True
        self.video = False
        self.plugin = plugin

    def list_items(self, sort=False):
        if sort:
            xbmcplugin.addSortMethod(self.plugin.addon_handle, sort)
        xbmcplugin.endOfDirectory(self.plugin.addon_handle, cacheToDisc=self.cache)

    def add_item(self, item):
        artist = self.plugin.utfenc(item.get('artist', ''))
        title = self.plugin.utfenc(item.get('title', artist))
        data = {
            'mode': item.get('mode', 'home'),
            'site': item.get('site', ''),
            'artist': artist,
            'title': title,
            'id': item.get('id', ''),
            'params': item.get('params','')
        }

        art = {
            'thumb': item.get('thumb', self.plugin.addon_icon),
            'poster': item.get('thumb', self.plugin.addon_icon),
            'fanart': item.get('fanart', self.plugin.addon_fanart)
        }

        labels = {
            'title': title,
            'plot': item.get('plot', title),
            'premiered': item.get('date', ''),
            'episode': item.get('episode', 0)
        }

        listitem = xbmcgui.ListItem(title)
        listitem.setArt(art)
        listitem.setInfo(type='Video', infoLabels=labels)

        if item.get('mode') == 'play_video':
            self.cache = False
            self.video = True
            folder = False
            data['title'] = '{0} - {1}'.format(artist, title)
            listitem.addStreamInfo('video', {'duration':item.get('duration', 0)})
            listitem.setProperty('IsPlayable', 'true')
        else:
            folder = True

        if item.get('cm', None):
            listitem.addContextMenuItems( item['cm'] )

        xbmcplugin.addDirectoryItem(self.plugin.addon_handle, self.plugin.build_url(data), listitem, folder)

    def play_item(self, title, path, resolved):
        listitem = xbmcgui.ListItem()
        listitem.setContentLookup(False)
        listitem.setMimeType('video/mp4')
        listitem.setInfo('video', {'Title': title})
        listitem.setPath(path)
        xbmcplugin.setResolvedUrl(self.plugin.addon_handle, resolved, listitem)

    def queue_item(self, title, thumb, params):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        listitem = xbmcgui.ListItem(title)
        listitem.setArt({'thumb': thumb})
        listitem.setProperty('IsPlayable', 'true')
        playlist.add(params, listitem)
