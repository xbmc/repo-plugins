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
import urllib
import xbmc
import re
import common

ROOT     = 'http://www.last.fm/music/'
NAME     = 'Last.FM'
REQUESTS = 3


def GetImages(artist):
    if artist == '':
        return []

    artist = artist.upper().replace(',','+').replace('(','+').replace(')','').replace('  ',' ').replace(' ','+')
    artist = artist.replace('++', '+')

    images = DoGetImages(artist)
    if len(images) == 0:
        images = DoGetImages(Reverse(artist))

    if len(images) == 0:
        if artist != 'THE+THE' and artist != 'THE':
            artist = artist.replace('THE+', '').replace('THE', '')
            images = DoGetImages(artist)
            if len(images) == 0:
                images = DoGetImages(Reverse(artist))

    #print NAME + ' Found - %d images' % len(images)
    return images


def DoGetImages(artist):
    try:
        images = []
        total  = GetTotal(artist)
        pages  = GetRandomPage(total)

        for page in range(0, len(pages)):
            url = ROOT + artist +'/+images?page=%d' % pages[page]
            
            link = common.GetHTML(url)

            match = re.compile('<a href="/music/(.+?)"').findall(link)

            for img in match:            
                try:
                    id  = int(img.rsplit('/', 1)[1])
                    img = 'http://userserve-ak.last.fm/serve/500/' + str(id) + '.jpg'
                    if img not in images:
                        images.append(img)
                except:
                    pass            

            if len(images) == 0:
                return images

    except Exception, e:
        pass

    return images


def GetTotal(artist):
    #url   = ROOT + artist +'/+images
    url   = ROOT + artist +'/+images?page=1'
    total = 1

    try:
        html  = common.GetHTML(url)
        if html == '':
            return 0

        match = re.compile('\?page=(\d+)"').findall(html)
        for item in match:
            n = int(item)
            if total < n:
                total = n
    except:
        pass

    return total


def GetRandomPage(total):
    pages  = []
    length = total
    max    = REQUESTS - 1

    if length > REQUESTS:
        length = REQUESTS

    import random

    #this isn't hugely efficient, but I can't see it ever being a problem
    while len(pages) < length:
        page = random.randrange(1, total+1)
        if page not in pages:
            pages.append(page)

    return pages


def Reverse(artist):
    reverse = ''
    split   = artist.split('+')
    for item in split:
        reverse = item + '+' + reverse
    reverse = reverse[:-1]
    return reverse