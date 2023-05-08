# -*- coding: utf-8 -*-

# Copyright 2022 Christian Prasch
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
# This file is derived from libardnewjsonparser.py from sarbes
# https://github.com/sarbes/script.module.libard

import xbmcaddon
import json
import time
import requests
import hashlib
import xbmc
import datetime
import re
#import web_pdb

ADDON_ID = 'plugin.video.weltspiegel'
apiUrl = 'https://api.ardmediathek.de/page-gateway/widgets/daserste/asset/Y3JpZDovL2Rhc2Vyc3RlLmRlL3dlbHRzcGllZ2Vs?pageNumber=0&pageSize=200&embedded=true'
apiUrlVideo = 'https://api.ardmediathek.de/page-gateway'
headers = {'content-type':'application/json'}

addon = xbmcaddon.Addon(id=ADDON_ID)
#web_pdb.set_trace()
showdate = addon.getSettingBool('ShowDate')

class parser:
    def __init__(self):
        self.result = {'items':[], 'content':'videos', 'pagination':{'currentPage':0}}
        self.deviceType = 'pc'

    def setContend(self,content):
        self.result['content'] = content

    def setParams(self,params):
        self.params = params
        
    def setPlugin(self,plugin):
        self.plugin = plugin

    def parseDefaultPage(self, client='daserste', select='all'):
        j = requests.get(f'{apiUrl}',headers=headers).json()
        
        if select == 'shows':
            for teaser in j['teasers']:
                #xbmc.log('Duration: '+ teaser['shortTitle'] + '   ' + str(teaser['duration']), xbmc.LOGDEBUG)
                if (teaser['duration'] > 2400) and (teaser['duration'] < 3000):
                    self._grabTeaser(teaser,client)
        elif select == 'report':
            for teaser in j['teasers']:
                if teaser['shortTitle'].lower().startswith('weltspiegel-reportage:'):
                    self._grabTeaser(teaser,client)
        elif select == 'extra':
            for teaser in j['teasers']:
                if teaser['shortTitle'].lower().startswith('weltspiegel extra:'):
                    self._grabTeaser(teaser,client)
        elif select == 'videos':
            for teaser in j['teasers']:
                if not (teaser['shortTitle'].startswith('Die Sendung vom') or \
                        teaser['shortTitle'].startswith('Weltspiegel vom') or \
                        teaser['shortTitle'].startswith('Sendung vom') or \
                        teaser['shortTitle'].lower().startswith('weltspiegel-reportage:') or \
                        teaser['shortTitle'].lower().startswith('weltspiegel extra:')):
                    self._grabTeaser(teaser,client)
        else:   # all
            for teaser in j['teasers']:
                self._grabTeaser(teaser,client)
                            
        return self.result

    def parseVideo(self,clipId='',client="ard"):
        j = requests.get(f'{apiUrlVideo}/mediacollection/{clipId}?devicetype={self.deviceType}',headers=headers).json()
        for item in j['_mediaArray'][0]['_mediaStreamArray']:
            if item['_quality'] == 'auto':
                url = item['_stream']
        if url.startswith('//'): 
            url = 'http:' + url
        d = {'media':[{'url':url, 'stream':'HLS'}]}
        if '_subtitleUrl' in j:
            d['subtitle'] = [{'url':j['_subtitleUrl'], 'type':'ttml', 'lang':'de', 'colour':True}]
        return d

    def _parse_date(self, isodate):
        """Parses the given date in iso format into a datetime."""
        if(not isodate):
            return None
        isodate = isodate[:-1]
        return datetime.datetime(*list(map(int, re.split('[^\d]', isodate))))

    def _grabTeaser(self,teaser,client=False):
        date = self._parse_date( teaser['broadcastedOn'] )
        datestr = date.strftime('%d.%m.%y')
        
        d = {'params':{}, 'metadata':{'art':{}}}
        
        d['metadata']['name'] = teaser['shortTitle']
        if showdate:
            d['metadata']['name'] = datestr + ':  ' + d['metadata']['name']

        d['metadata']['plotoutline'] = teaser['longTitle']
        if 'shortSynopsis' in teaser:
            d['metadata']['plotoutline'] = teaser['shortSynopsis']
        d['metadata']['plotoutline'] = datestr + '\n' + d['metadata']['plotoutline']

        if 'synopsis' in teaser:
            d['metadata']['plot'] = teaser['synopsis']
        if 'duration' in teaser:
            d['metadata']['duration'] = teaser['duration']
        if 'images' in teaser:
            if 'aspect16x9' in teaser['images']:
                d['metadata']['art']['thumb'] = teaser['images']['aspect16x9']['src'].format(width='512')
            if 'aspect3x4' in teaser['images']:
                d['metadata']['art']['poster'] = teaser['images']['aspect3x4']['src'].format(width='512')
        if 'show' in teaser and 'images' in teaser['show'] and '16x9' in teaser['show']['images']:
            d['metadata']['art']['fanart'] = teaser['show']['images']['16x9']['src'].format(width='512')
        if client:
            d['params']['client'] = client
        if teaser['type'] == 'compilation':
            d['params']['compilationId'] = teaser['links']['target']['id']
            d['type'] = 'dir'
            #d['params']['mode'] = 'ListMorePage'
        elif teaser['type'] == 'show':
            d['params']['showId'] = teaser['links']['target']['id']
            d['type'] = 'dir'
            #d['params']['mode'] = 'ListShow'
        elif teaser['type'] == 'poster':
            d['type'] = 'movie'
            d['params']['mode'] = 'Play'
        elif teaser['type'] == 'broadcastMainClip':
            d['type'] = 'date'
            d['params']['mode'] = 'Play'
        else:
            d['type'] = 'video'
            d['params']['mode'] = 'Play'

        if 'broadcastedOn' in teaser:
            d['metadata']['aired'] = {'ISO8601':teaser['broadcastedOn']}

        
        if 'subtitled' in teaser:
            d['metadata']['hassubtitles'] = True

        if 'links' in teaser and 'target' in teaser['links'] and 'id' in teaser['links']['target']:
            d['params']['id'] = teaser['links']['target']['id']
            self.result['items'].append(d)
        return
