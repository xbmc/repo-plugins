import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmc
import json,urllib



def playVideo(jslist):
    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    pl.clear()
    for u in jslist:
        pl.add("http://openings.moe/video/"+u['file'], xbmcgui.ListItem(u['source']+" "+u['title']))
    pl.shuffle()
    xbmc.Player().play(pl, windowed=False)

if __name__ == '__main__':
    data = urllib.urlopen("http://openings.moe/api/list.php").read()
    output = json.loads(data)
    playVideo(output)