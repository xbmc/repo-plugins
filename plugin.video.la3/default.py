#!/usr/bin/python
import os, requests
from neverwise import Util

li = Util.createListItem(Util._addonName, thumbnailImage = '{0}/icon.png'.format(os.path.dirname(os.path.abspath(__file__))), streamtype = 'video', infolabels = { 'title' : Util._addonName })
url1 = 'http://h3ghdchan102-i.akamaihd.net/hls/live/217154/Virtual_Channel102/master.m3u8'
url2 = 'http://h3ghdchan102-i.akamaihd.net/hls/live/217154-b/Virtual_Channel102/master.m3u8'

request = requests.get(url1)
if request.status_code == 200:
  xbmc.Player().play(url1, li)
else:
  request = requests.get(url2)
  if request.status_code == 200:
    xbmc.Player().play(url2, li)
