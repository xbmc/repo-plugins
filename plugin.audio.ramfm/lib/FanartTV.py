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
import re
import common

ROOT = 'http://fanart.tv/'
NAME = 'Fanart.TV'

def GetImages(artist):
    if artist == '':
        return []

    artist = artist.upper().replace(' & ',' ').replace(',','+').replace('(','').replace(')','').replace(' ','+')
    artist = artist.replace('++', '+')

    try:
        url    = ROOT + 'api/getdata.php?type=2&s=' + artist
        images = []

        #print NAME + ' 1st URL requested: %s' % url
        link = common.GetHTML(url)

        max = -1
        url = None

        match = re.compile('<div class="item-name"><a href="/(.+?)".+?<span class="pop">(.+?)</span>').findall(link)
        for link, qty in match:
            qty = int(qty)
            if max < qty:
                max = qty
                url = link

        if not url:
            return images

        url = ROOT + url
    
        #print NAME + ' 2nd URL requested: %s' % url
        link = common.GetHTML(url)

        match = re.compile('href="/fanart/(.+?).(?:jpg|png|jpeg|JPG)"').findall(link)

        for img in match:
            if img + '.jpg' in link:
                images.append(ROOT+'fanart/'+img+'.jpg')
            elif img + '.JPG' in link:
                images.append(ROOT+'fanart/'+img+'.JPG')
            elif img + '.jpeg' in link:
                images.append(ROOT+'fanart/'+img+'.jpeg')
    except Exception, e:
        pass

    #print NAME + ' Found - %d images' % len(images)
    return images