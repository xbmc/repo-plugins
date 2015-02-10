#
#      Copyright (C) 2013 Sean Poyser
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import urllib2
import sys
import re
import common


#if sys.version_info >=  (2, 7):
#    import json
#else:
#    import simplejson as json 
import json
if not 'load' in dir(json):
    import simplejson as json


ROOT   = 'http://www.theaudiodb.com/api/v1/json/'
API    = '58424d43204d6564696120'
SEARCH = ROOT + API + '/search.php?s='
NAME   = 'TheAudio.DB'


def GetImages(artist):
    if artist == '':
        return []

    artist = artist.upper().replace(' & ',' ').replace(',','+').replace('(','').replace(')','').replace(' ','+')
    artist = artist.replace('++', '+')

    images = DoGetImages(artist)

    if len(images) < 1:
        reverse = ''
        split   = artist.split('+')
        for item in split:
            reverse = item + '+' + reverse
        reverse = reverse[:-1]

        images = DoGetImages(reverse)

    #print NAME + ' Found - %d images' % len(images)
    return images


def DoGetImages(artist):
    try:
        url = SEARCH + artist

        images = []

        #print NAME + ' 1st URL requested: %s' % url           
        link = common.GetHTML(url)
        link = link.replace(',',  '\n')

        matchJPG = re.compile('http(.+?).jpg').findall(link)
        #matchPNG = re.compile('http(.+?).png').findall(link)

        for img in matchJPG:
            img = 'http' + img + '.jpg'
            images.append(img)

        #PNG don't work in XBMC slideshow
        #for img in matchPNG:
        #    img = 'http' + img + '.png'
        #    images.append(img)

    except Exception, e:
        pass
    
    return images