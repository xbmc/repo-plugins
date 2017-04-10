import xbmc
import xbmcgui
import xbmcaddon

listitem =xbmcgui.ListItem ('Videolina')
listitem.setInfo('video', {'Title': 'Videolina', 'Genre': ''})
xbmc.Player().play('http://178.33.229.111/live/Videolina/playlist.m3u8', listitem, False)