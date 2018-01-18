# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin

class Items:

    def __init__(self, plugin):
        self.cache = True
        self.video = False
        self.plugin = plugin

    def list_items(self, sort=False, upd=False):
        if self.video:
            xbmcplugin.setContent(self.plugin.addon_handle, self.plugin.content)
        if sort:
            xbmcplugin.addSortMethod(self.plugin.addon_handle, 1)
        xbmcplugin.endOfDirectory(self.plugin.addon_handle, cacheToDisc=self.cache, updateListing=upd)

        if self.plugin.force_view:
            xbmc.executebuiltin('Container.SetViewMode({0})'.format(self.plugin.view_id))

    def add_item(self, item):
        data = {
            'mode': item['mode'],
            'title': item['title'],
            'id': item.get('id', ''),
            'params': item.get('params', '')
        }

        art = {
            'thumb': item.get('thumb', self.plugin.addon_fanart),
            'poster': item.get('thumb', self.plugin.addon_fanart),
            'fanart': item.get('fanart', self.plugin.addon_fanart)
        }

        labels = {
            'title': item['title'],
            'plot': item.get('plot', item['title']),
            'premiered': item.get('date', ''),
            'episode': item.get('episode', 0)
        }

        listitem = xbmcgui.ListItem(item['title'])
        listitem.setArt(art)
        listitem.setInfo(type='Video', infoLabels=labels)

        if 'play' in item['mode']:
            self.cache = False
            self.video = True
            folder = False
            listitem.addStreamInfo('video', {'duration':item.get('duration', 0)})
            listitem.setProperty('IsPlayable', 'true')
        else:
            folder = True

        if item.get('cm', None):
            listitem.addContextMenuItems( item['cm'] )

        xbmcplugin.addDirectoryItem(self.plugin.addon_handle, self.plugin.build_url(data), listitem, folder)
        
    def play_item(self, path, license_key):
        listitem = xbmcgui.ListItem()
        listitem.setContentLookup(False)
        listitem.setMimeType('application/x-mpegURL')
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.license_key', license_key)
        listitem.setPath(path)
        xbmcplugin.setResolvedUrl(self.plugin.addon_handle, True, listitem)
        
    def add_token(self, license_key):
        listitem = xbmcgui.ListItem()
        xbmcplugin.addDirectoryItem(self.plugin.addon_handle, license_key, listitem)
        xbmcplugin.endOfDirectory(self.plugin.addon_handle, cacheToDisc=False)