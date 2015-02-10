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

ROOT   = 'http://htbackdrops.org/api/'
API    = '96d681ea0dcb07ad9d27a347e64b652a'
SEARCH = ROOT + API + '/searchXML?inc=images&default_operator=and&keywords='
NAME   = 'HTBackdrops'


def GetImages(artist):
    if artist == '':
        return []

    artist = artist.upper().replace(' & ',' ').replace(',','+').replace('(','').replace(')','').replace(' ','+')
    artist = artist.replace('++', '+')

    try:
        url = SEARCH + artist#.replace('+', ' ')

        images = []

        #print NAME + ' 1st URL requested: %s' % url           
        link = common.GetHTML(url)

        match = re.compile('<id>(.+?)</id>').findall(link)

        for id in match:
            img = ROOT + API + '/download/' + id  + '/fullsize'
            images.append(img)

    except Exception, e:
        pass

    #print NAME + ' Found - %d images' % len(images)
    return images