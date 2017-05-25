#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Original Work Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#     Modified Work Copyright (C) 2016 Edison Yau (gedisony@gmail.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import random
import sys

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

import xbmc
import xbmcaddon
import xbmcvfs
import re
import urllib
from xbmcgui import ControlImage, WindowDialog

addon = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo('name')
ADDON_PATH = addon.getAddonInfo('path')

default_frontpage    = addon.getSetting("screensaver_subreddit")
sitemsPerPage        = addon.getSetting("itemsPerPage")
try: itemsPerPage = int(sitemsPerPage)
except: itemsPerPage = 50    
itemsPerPage          = ["10", "25", "50", "75", "100"][itemsPerPage]


def this_is_a_multihub(subreddit):
    #subreddits and multihub are stored in the same file
    #i think we can get away with just testing for user/ to determine multihub
    if subreddit.lower().startswith('user/') or subreddit.lower().startswith('/user/'): #user can enter multihub with or without the / in the beginning
        return True
    else:
        return False
    
def assemble_reddit_filter_string(subreddit, domain="" ):
    url = "https://www.reddit.com"

    if subreddit.startswith('?'):
        #special dev option
        url+='/search.json'+subreddit 
        return url

    if subreddit.startswith('http'):
        #special dev option2 
        #url=subreddit.replace('/search', '/search.json')  
        url=subreddit
        return url


    a=[':','/domain/']
    if any(x in subreddit for x in a):  #search for ':' or '/domain/'
        #log("domain "+ subreddit)
        domain=re.findall(r'(?::|\/domain\/)(.+)',subreddit)[0]
        #log("domain "+ str(domain))

    if domain:
        # put '/?' at the end. looks ugly but works fine.
        #https://www.reddit.com/domain/vimeo.com/?&limit=5
        url+= "/domain/%s/.json?" %(domain)   #/domain doesn't work with /search?q=
    else:
        if this_is_a_multihub(subreddit):
            #e.g: https://www.reddit.com/user/sallyyy19/m/video/search?q=multihub&restrict_sr=on&sort=relevance&t=all
            #https://www.reddit.com/user/sallyyy19/m/video
            #url+='/user/sallyyy19/m/video'     
            #format_multihub(subreddit)
            if subreddit.startswith('/'):
                url+=subreddit  #user can enter multihub with or without the / in the beginning
            else: url+='/'+subreddit
        else:
            if subreddit: 
                url+= "/r/"+subreddit
 
        site_filter=""
        url+= "/.json?"

    url += "&limit="+str(itemsPerPage)
    return url

if __name__ == '__main__':
    randomize=""
    reddit_url=assemble_reddit_filter_string(default_frontpage )

    #xbmc.executescript("script.reddit.reader,mode=autoSlideshow&url=https%3A%2F%2Fwww.reddit.com%2F.json%3F%26nsfw%3Ano%2B%26limit%3D10&name=&type=")
    xbmc.executebuiltin("RunAddon(script.reddit.reader,mode=autoSlideshow&url=%s&name=&type=%s)" %(urllib.quote_plus(reddit_url), '') )
        

