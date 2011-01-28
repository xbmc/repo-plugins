# -*- coding: utf-8 -*-
# Copyright 2010 Jörn Schumacher 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import urllib2, re

import xbmcplugin, xbmcgui

# urls
# these urls refer to rss feeds
urls = dict()
urls['ts100s'] = 'http://www.tagesschau.de/export/video-podcast/tagesschau-in-100-sekunden/'
urls['ts20h'] = 'http://www.tagesschau.de/export/video-podcast/webl/tagesschau/'

# regular expressions
# Since the urls refer to rss-feeds, it might be better to 
# do some real xml-parsing, but it works for now.
regexp = dict()
regexp['ts100s'] = dict()
regexp['ts100s']['date'] = r'<title>(.*) - .*</title>'
regexp['ts100s']['url'] = r'<enclosure url="(.*)"\slength.*'


regexp['ts20h'] = dict()
regexp['ts20h']['date'] = r'<title>tagesschau (.*)</title>'
regexp['ts20h']['url'] = r'<enclosure url="(.*)"\slength.*'



def get_video_ts100s():
    # config
    url = 'http://www.tagesschau.de/multimedia/video/ondemand100.html'
    pattern = r'<a href="(.*\.webl\.h264\.mp4)".*>'
    date_pattern = r'<span class="topline">(\S*)\s*(\S*)\s*Uhr</span>'

    # parse the website
    s = urllib2.urlopen(url).read()
    video = re.compile(pattern).findall(s)[0]

    # fetch the date from the website
    date = re.compile(date_pattern).findall(s)[0]
    date = date[0]+', '+date[1]+' Uhr'

    # return video+date
    return date, video

def get_video_ts20h():
    # config
    url = 'http://www.tagesschau.de/multimedia/video/ondemandarchiv100.html'
    pattern = r'<a href="(.*\.webl\.h264\.mp4)".*>'

    date_pattern = r'TV-(\d\d\d\d)(\d\d)(\d\d)'

    # parse the website
    s = urllib2.urlopen(url).read()
    video = re.compile(pattern).findall(s)[0]

    # fetch the date from the video url
    date = re.compile(date_pattern).findall(video)[0]
    date = '.'.join((date[2], date[1], date[0])) + ', 20:00 Uhr'

    # return video+date
    return date, video

def get_video_tt():
    url = 'http://www.tagesschau.de/export/video-podcast/webl/tagesthemen/'
    pattern = r'url="(.*\.webl\.h264\.mp4)"'

    date_pattern = r'<title>tagesthemen (\S*)\s*Uhr,\s*(\S*)</title>'    
     
    # parse the website
    s = urllib2.urlopen(url).read()
    video = re.compile(pattern).findall(s)[0]
    
    # fetch the date from the video url
    date = re.compile(date_pattern).findall(s)[0]
    date = date[1]+', '+date[0]+' Uhr'
    
    # return video+date
    return date, video


def addLink(name,url,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

items = []

date, url = get_video_ts20h()
addLink('Tagesschau ('+date+')', url, 'http://www.tagesschau.de/image/podcast/ts-140.jpg')

date, url = get_video_ts100s()
addLink('Tagesschau in 100 Sekunden ('+date+')', url, 'http://www.tagesschau.de/image/podcast/ts100s-140.jpg')

date, url = get_video_tt()
addLink('Tagesthemen ('+date+')', url, 'http://www.tagesschau.de/image/podcast/tt-140.jpg')

xbmcplugin.endOfDirectory(int(sys.argv[1]))
