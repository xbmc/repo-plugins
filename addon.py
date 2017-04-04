import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import logging
from operator import itemgetter

listitem =xbmcgui.ListItem ('Videolina')
listitem.setInfo('video', {'Title': 'Videolina', 'Genre': ''})
xbmc.Player().play('http://178.33.229.111/live/Videolina/playlist.m3u8', listitem, False)
