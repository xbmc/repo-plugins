# -*- coding: utf-8 -*-
import xbmc
from swiftwrap import Plugin

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

PLUGIN = Plugin()

LIVE_PREVIEW_IMAGE = '%://static-cdn.jtvnw.net/previews-ttv/live_user_%-%___x%___.jpg'  # sqlite LIKE pattern


class Images(object):
    ICON = xbmc.translatePath('special://home/addons/%s/icon.png' % PLUGIN.id)
    THUMB = xbmc.translatePath('special://home/addons/%s/icon.png' % PLUGIN.id)
    POSTER = xbmc.translatePath('special://home/addons/%s/icon.png' % PLUGIN.id)
    FANART = xbmc.translatePath('special://home/addons/%s/fanart.jpg' % PLUGIN.id)
    BANNER = ''
    CLEARART = ''
    CLEARLOGO = ''
    LANDSCAPE = ''
    #
    VIDEOTHUMB = 'http://static-cdn.jtvnw.net/ttv-static/404_preview-320x180.jpg'
    BOXART = 'http://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg'
