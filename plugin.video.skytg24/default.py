#!/usr/bin/python
import os
from neverwise import Util

li = Util.createListItem(Util._addonName, thumbnailImage = '{0}/icon.png'.format(os.path.dirname(os.path.abspath(__file__))), streamtype = 'video', infolabels = { 'title' : Util._addonName })
# rtmp://cp49989.live.edgefcs.net:1935/live/streamRM1@2564 app=live playpath=streamRM1@2564 swfUrl=http://videoplatform.sky.it/player/swf/player_v2.swf pageURL=http://video.sky.it/news/diretta swfVfy=true live=true timeout=30 flashVer=LNX 11,2,202,297
xbmc.Player(xbmc.PLAYER_CORE_MPLAYER).play('rtmp://cp49989.live.edgefcs.net:1935/live/streamRM1@2564 live=true', li)
