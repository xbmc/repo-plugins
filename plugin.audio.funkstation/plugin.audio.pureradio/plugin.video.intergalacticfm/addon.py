import xbmc
import xbmcgui


__author__ = 'Pander'


# Stream URL
# url = 'http://95.211.225.124:1935/SFLive/prc/playlist.m3u8'  # archive
url = 'http://intergalactic.tv:1935/live/prc/playlist.m3u8'  # live
# Fake List Item for Stream Name
listitem = xbmcgui.ListItem('Intergalactic FM TV')
listitem.setInfo(
    'video', {'Title': 'Intergalactic FM TV', 'Genre': 'Music Video'})
# Play the Stream
xbmc.Player().play(url, listitem)
