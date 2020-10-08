# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011-2020 jackyNIX

This file is part of KODI Mixcloud Plugin.

KODI Mixcloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KODI Mixcloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with KODI Mixcloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''



from .utils import Utils
from .history import History
from .mixcloud import MixcloudInterface
from .base import BaseBuilder
from .lang import Lang
from urllib import request, parse
import xbmc
import xbmcgui
import xbmcplugin
import re
import sys
import json
import base64
from itertools import cycle



STR_USERAGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'



class BaseResolver:

    def __init__(self, key):
        self.key = key

    def resolve(self):
        return ''



class MixcloudResolver(BaseResolver):

    def resolve(self):
        url = None
        ck = 'https://www.mixcloud.com' + self.key
        Utils.log('resolving cloudcast stream via mixcloud: ' + ck)

        try:
            keysplit = self.key.split('/')
            Utils.log('keysplit [empty, username, slug, empty] = %s' % (keysplit))

            # get crsf token
            csrf_token = None
            response = request.urlopen('https://www.mixcloud.com')
            headers = response.info()
            for header in headers.get_all('Set-Cookie', []):
                attributes = header.split('; ')
                for attribute in attributes:
                    pair = attribute.split('=')
                    if pair[0] == 'csrftoken':
                        csrf_token = pair[1]
            Utils.log('csrf_token = %s' % (csrf_token))

            # create graphql
            graphql = {
                'query' : 'query HeaderQuery(\n  $lookup: CloudcastLookup!\n) {\n  cloudcast: cloudcastLookup(lookup: $lookup) {\n    id\n    isExclusive\n    ...PlayButton_cloudcast\n  }\n}\n\nfragment PlayButton_cloudcast on Cloudcast {\n  streamInfo {\n    hlsUrl\n    dashUrl\n    url\n    uuid\n  }\n}\n',
                'variables' : {
                    'lookup' : {
                        'username' : keysplit[1],
                        'slug' : keysplit[2]
                    }
                }
            }
            Utils.log('graphql = %s' % (graphql))

            # request graphql
            postdata = json.dumps(graphql).encode()
            headers = {
                'Referer' : 'https://www.mixcloud.com',
                'X-CSRFToken' : csrf_token,
                'Cookie' : 'csrftoken=' + csrf_token,
                'Content-Type' : 'application/json'
            }

            req = request.Request('https://www.mixcloud.com/graphql', postdata, headers, 'https://www.mixcloud.com')
            response = request.urlopen(req)
            content = response.read()
            json_content = json.loads(content)
            Utils.log('response = %s' % (json_content))

            # parse json
            json_isexclusive=False
            json_url=None
            if 'data' in json_content and json_content['data']:
                json_data = json_content['data']
                if 'cloudcast' in json_data and json_data['cloudcast']:
                    json_cloudcast = json_data['cloudcast']
                    if 'isExclusive' in json_cloudcast and json_cloudcast['isExclusive']:
                        json_isexclusive = json_cloudcast['isExclusive']
                    if 'streamInfo' in json_cloudcast and json_cloudcast['streamInfo']:
                        json_streaminfo = json_cloudcast['streamInfo']
                        if 'url' in json_streaminfo and json_streaminfo['url']:
                            json_url = json_streaminfo['url']
                        elif 'hlsUrl' in json_streaminfo and json_streaminfo['hlsUrl']:
                            json_url = json_streaminfo['hlsUrl']
                        elif 'dashUrl' in json_streaminfo and json_streaminfo['dashUrl']:
                            json_url = json_streaminfo['dashUrl']

            if json_url:
                Utils.log('encoded url: ' + json_url)
                decoded_url = base64.b64decode(json_url).decode('utf-8')
                url = ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(decoded_url, cycle('IFYOUWANTTHEARTISTSTOGETPAIDDONOTDOWNLOADFROMMIXCLOUD')))
                Utils.log('url found: ' + url)
                if not Utils.isValidURL(url):
                    Utils.log('invalid url')
                    url = None
            elif json_isexclusive:
                Utils.log('Cloudcast is exclusive')
            else:
                Utils.log('Unable to find url in json')

        except Exception as e:
            Utils.log('Unable to resolve', e)
        return url



class MixcloudDownloaderResolver(BaseResolver):

    def resolve(self):
        url = None
        ck = 'https://www.mixcloud.com' + self.key
        Utils.log('resolving cloudcast stream via mixcloud-downloader: ' + ck)

        try:
            headers = {
                'User-Agent' : STR_USERAGENT,
                'Referer' : 'https://www.mixcloud-downloader.com/'
            }

            values = {
                'url' : ck,
            }
            postdata = parse.urlencode(values).encode('utf-8')
            req = request.Request('https://www.mixcloud-downloader.com/download/', postdata, headers, 'https://www.mixcloud-downloader.com/')
            response = request.urlopen(req)
            data = response.read().decode('utf-8')

            # first attempt
            match = re.search(r'a class="btn btn-secondary btn-sm"(.*)', data, re.DOTALL)
            if match:
                match=re.search(r'href="(.*)"', match.group(1))
                if match:
                    url = match.group(1)
                    Utils.log('url found (1): ' + url)
                    if not Utils.isValidURL(url):
                        Utils.log('invalid url')
                        url = None
                else:
                    Utils.log('Wrong response code (1)=%s len=%s' % (response.getcode(), len(data)))

            # second attempt
            if not url:
                match = re.search(r'URL from Mixcloud: <br /> <a href="(.*)"', data)
                if match:
                    url = match.group(1)
                    Utils.log('url found (2): ' + url)
                    if not Utils.isValidURL(url):
                        Utils.log('invalid url')
                        url = None
                else:
                    Utils.log('Wrong response code (2)=%s len=%s' % (response.getcode(), len(data)))
        except Exception as e:
            Utils.log('Unable to resolve: ', e)
        return url



class OfflibertyResolver(BaseResolver):

    def resolve(self):
        url = None
        ck = 'https://www.mixcloud.com' + self.key

        mon = xbmc.Monitor()            
        for retry in range(1, 2):
            # user aborted
            if mon.abortRequested():
                break
                
            Utils.log('resolving cloudcast stream via offliberty (' + str(retry) + '): ' + ck)

            try:
                values = {
                    'url' : ck
                }
                headers = {
                    'User-Agent' : STR_USERAGENT
                }
                getparams = parse.urlencode(values)
                req = request.Request('https://offliberty.online/download?' + getparams, headers = headers)
                response = request.urlopen(req)
                data = response.read().decode('utf-8')
                match = re.search(r'href="(.*)" download="', data)
                if match:
                    url = match.group(1)
                    Utils.log('url found: ' + url)
                    if not Utils.isValidURL(url):
                        Utils.log('invalid url')
                        url = None
                else:
                    Utils.log('Wrong response try=%s code=%s len=%s, trying again...' % (retry, response.getcode(), len(data)))
            except Exception as e:
                Utils.log('Unexpected error try=%s error=%s, trying again...' % (retry, sys.exc_info()[0]), e)
        return url



class ResolverBuilder(BaseBuilder):

    def execute(self):
        Utils.log('ResolverBuilder.execute()')
        url = self.getStream()
        if url:
            mixcloudListItem = MixcloudInterface().getCloudcast(self.key, {})
            if mixcloudListItem:
                listitem = xbmcgui.ListItem(label = mixcloudListItem.infolabels['title'], label2 = mixcloudListItem.infolabels['artist'], path = url)
                listitem.setInfo('music', mixcloudListItem.infolabels)
                xbmcplugin.setResolvedUrl(handle = self.plugin_handle, succeeded = True, listitem = listitem)
                History.getHistory('play_history').add({'key' : self.key})
                Utils.log('Playing: ' + url)
                return
        Utils.log('Stop player')
        xbmcplugin.setResolvedUrl(handle = self.plugin_handle, succeeded = False, listitem = xbmcgui.ListItem())

    def getStream(self):
        Utils.log('ResolverBuilder.getStream()')

        strm_url = None

        # resolvers
        activeResolvers = []
        if Utils.getSetting('resolver_mixcloud') == 'true':
            activeResolvers.append(MixcloudResolver)
        # todo: this resolvers is currently broken, uncomment when back online
        # if Utils.getSetting('resolver_mixclouddownloader') == 'true':
        #     activeResolvers.append(MixcloudDownloaderResolver)
        if Utils.getSetting('resolver_offliberty') == 'true':
            activeResolvers.append(OfflibertyResolver)
        Utils.log('active resolvers: ' + str(activeResolvers))

        if len(activeResolvers) > 0:
            mon = xbmc.Monitor()            
            for resolver in activeResolvers:
                # user aborted
                if mon.abortRequested():
                    break
                    
                strm_url = resolver(self.key).resolve()

                # stream found!
                if strm_url:
                    break
        else:
            xbmcgui.Dialog().ok('Mixcloud', Lang.NO_ACTIVE_RESOLVERS)

        return strm_url