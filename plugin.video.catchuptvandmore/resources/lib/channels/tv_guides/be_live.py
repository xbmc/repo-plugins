# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals
import urlquick
import json
import datetime
import time
from resources.lib.tzlocal import get_localzone
import pytz

URL_PROGRAMS = 'https://api-ctr.programme-tv.net/v2/broadcasts.json?' \
               'limit=auto&projection=id,title,startedAt,duration,isHD' \
               ',isNew,hasCatchup,hasDeafSubtitles,CSAAgeRestriction,' \
               'program%7Bid,rating,sportMatch,videos%7Bplatform,' \
               'providerUrl%7D,image%7BurlTemplate%7D,formatGenre%'\
               '7Bgenre%7Bname%7D%7D%7D,channel' \
               '%7Bid,title,image%7BurlTemplate%7D,darkImage' \
               '%7BurlTemplate%7D,' \
               'channelBouquets%7BchannelNumber,bouquet%7Bid,' \
               'isDefault%7D%7D%7D&bouquets=default&date=now'


ID_CHANNELS = {
   24: 'canvas',
   382: 'bx1',
   387: 'telemb',
   390: 'rtc',
   392: 'tvlux',
   1280: 'ketnet',
   23: 'een'
}

GUIDE_TIMEZONE = pytz.timezone('UTC')
GUIDE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def grab_tv_guide(channels):
    programs = {}

    guide_json = urlquick.get(
        URL_PROGRAMS,
        max_age=-1)
    guide_json = json.loads(guide_json.text)
    guide_items = guide_json['data']['items']

    for guide_item in guide_items:
        channel = guide_item['channel']
        channel_crt_id = channel['id']

        if channel_crt_id in ID_CHANNELS and \
                ID_CHANNELS[channel_crt_id] in channels:

            channel_id = ID_CHANNELS[channel_crt_id]
            program_dict = {}

            program_dict['duration'] = guide_item['duration']  # sec

            start_s = guide_item['startedAt']
            start_s = start_s.split('+')[0]

            try:
                start = datetime.datetime.strptime(
                    start_s,
                    GUIDE_TIME_FORMAT)
            except TypeError:
                start = datetime.datetime(*(time.strptime(
                    start_s, GUIDE_TIME_FORMAT)[0:6]))

            try:
                local_tz = get_localzone()
            except:
                # Hotfix issue #102
                local_tz = pytz.timezone('Europe/Brussels')
            
            start = GUIDE_TIMEZONE.localize(start)
            start = start.astimezone(local_tz)
            start_time = start.strftime("%Hh%M")

            program_dict['start_time'] = start_time

            program_dict['genre'] = guide_item['program']['formatGenre']['genre']['name']

            program_dict['program_id'] = guide_item['id']

            program_dict['title'] = guide_item['title']

            # https://tel.img.pmdstatic.net/fit/http.3A.2F.2Fimages.2Eone.2Eprismamedia.2Ecom.2Fchannel.2F2.2F3.2F9.2Fe.2F1.2F3.2F1.2Fb.2Ff.2Fd.2Fa.2F0.2F2.2Fa.2F3.2Fd.2Epng/76x76/quality/100/image.png
            # https://tel.img.pmdstatic.net/fit/http.3A.2F.2Fimages.2Eone.2Eprismamedia.2Ecom.2Fprogram.2Fe.2F0.2F0.2F2.2F5.2Fc.2F3.2F3.2F2.2F1.2F1.2F1.2F1.2Fa.2F4.2F9.2Ejpg/520x336/quality/75/image.jpg
            # https://tel.img.pmdstatic.net/{transformation}/http.3A.2F.2Fimages.2Eone.2Eprismamedia.2Ecom.2Fprogram.2F8.2F0.2F4.2F4.2F4.2F7.2F9.2F3.2F5.2F4.2F9.2F7.2F4.2Fb.2Ff.2Fd.2Ejpg/{width}x{height}/{parameters}/{title}.jpg

            if 'image' in guide_item['program']:
                image = guide_item['program']['image']['urlTemplate']
                image = image.replace('{transformation}', 'fit')
                image = image.replace('{width}', '520')
                image = image.replace('{height}', '336')
                image = image.replace('{parameters}', 'quality/75')
                image = image.replace('{title}', 'image')
                program_dict['thumb'] = image

            programs[channel_id] = program_dict

    return programs


# Only for testing purpose
if __name__ == '__main__':
    grab_tv_guide({})


'''
Ciné revue IDs

303 ABXPLORE
79 Disney XD
12 Animaux
156 Rai Uno
473 Nickelodéon
243 National Geographic
417 Be Ciné
29 BE 1
652 Disney Cinema
80 France 3
1967 Disney Channel Wallonia
390 RTC Télé Liège
385 TV COM
389 Canal C
382 BX1
386 Canal Zoom
317 Ciné+ Frisson Belgique
393 MAtélé
516 Arte Belgique
1833 NoTélé
388 ACTV
383 Télé Sambre
391 Vedia
387 Télé MB
265 Melody
907 Mezzo Live HD
76 Eurosport 1
24 Canvas
1075 Proximus 11
912 NPO3
36 Cartoon Network
108 Q2
147 Planète+
294 Ciné+ Premier Belgique
482 Gulli
910 NPO1
833 Sundance TV
32 Canal J
405 E !
166 RTL Télévision
892 La Trois
205 TV5MONDE
832 Nick Jr
225 TvBreizh
164 La Une
7 Toute l'histoire
229 TIJI
23 één
212 Voyage
219 ZDF
168 RTL TVI
340 2M Monde
437 Ciné+ Classic Belgique
17 BBC 2
911 NPO2
192 TF1
197 TéléToon+
214 Vier
47 France 5
659 Vivolta
215 VTM
13 ARD
413 VOOsport World 1
15 AB Moteurs
16 BBC 1
125 Mezzo
187 La Deux
78 France 4
451 Ushuaïa TV
691 Vijf
1776 Trek
377 Plug RTL
914 Vitaya
254 AB 3
4 France 2
10 Action
128 MTV
400 Discovery Channel
38 Chasse et pêche
439 Eurosport 2
118 M6
169 RTPI
479 Syfy
50 Club RTL
232 TV5MONDE Europe
160 France Ô
446 TFX
185 TCM Cinéma
54 Comédie+
2 13eme RUE
1404 TF1 Séries Films
88 Histoire
472 VOOsport World 3
2024 Eleven Sports 1
2025 Eleven Sports 2
418 Be Séries
1280 Ketnet
414 VOOsport World 2
1144 Voo Foot
208 TVE
392 TV Lux
'''
