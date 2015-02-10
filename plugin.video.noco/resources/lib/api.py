#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2014 Julien Gormotte (jgormotte@ate.info)
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

import json, time
try:
    import requests2 as requests
except:
    import requests
from base64 import b64encode
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError, URLError, build_opener
from urlparse import urlparse,parse_qs
from random import randint
from xbmcswift2 import Plugin

mainURL = 'https://api.noco.tv/1.1/'
client_id = 'xbmc_gormux'
client_secret = '5a613e170e1613e512e8434dddcdb413'

plugin = Plugin()

class nocoApi():
    def get_token(self, user, password):
        loginrequest = urlencode({'username': user,
                                  'password': password,
                                  'login': '1'})
        requestHandler = build_opener()
        page = requestHandler.open(mainURL+"OAuth2/authorize.php?response_type=code&client_id="+client_id+"&state=STATE", loginrequest)
        ts = time.time()
        code = parse_qs(urlparse(page.geturl()).query)['code'][0]
        apirequest = urlencode({'grant_type': 'authorization_code',
                                'code': code})
        requestHandler = build_opener()
        requestHandler.addheaders = [('Authorization', b'Basic ' + b64encode(client_id + b':' + client_secret))]
        token = requestHandler.open(mainURL+"OAuth2/token.php", apirequest).read()
        data = json.loads(token)
        expire = time.time() + float(data['expires_in'])
        return str(data['access_token']), expire, str(data['refresh_token'])
    def renew_token(self, renew):
        apirequest = urlencode({'grant_type': 'refresh_token',
                                'refresh_token': renew})
        requestHandler = build_opener()
        requestHandler.addheaders = [('Authorization', b'Basic ' + b64encode(client_id + b':' + client_secret))]
        token = requestHandler.open(mainURL+"OAuth2/token.php", apirequest).read()
        data = json.loads(token)
        expire = time.time() + float(data['expires_in'])
        return str(data['access_token']), str(expire), str(data['refresh_token'])

    def get_partners(self, token):
        partners = []
        request = {'access_token': token, 'partner_key': ''}
        data = json.loads(requests.get(mainURL+'partners/subscribed', params=request).text)
        for element in data:
            if not element['nb_shows'] == None:
               partners.append(element) 
        return partners
    def get_themes(self, partner, token):
        data = []
        request = {'access_token': token, 'partner_key': partner, 'elements_per_page': '4000'}
        json_data = json.loads(requests.get(mainURL+'families', params=request).text)
        for element in json_data:
            if not any(d['theme_key'] == element['theme_key'] for d in data):
                data.append({'theme_key': element['theme_key'], 'theme_name': element['theme_name'], 'icon': element['icon_1024x576']})
        return data
    def get_types(self, partner, token):
        data = []
        request = {'access_token': token, 'partner_key': partner, 'elements_per_page': '4000'}
        json_data = json.loads(requests.get(mainURL+'families', params=request).text)
        for element in json_data:
            if not any(d['type_key'] == element['type_key'] for d in data):
                data.append({'type_key': element['type_key'], 'type_name': element['type_name'], 'icon': element['icon_1024x576']})
        return data
    def get_all(self, partner, token):
        data = []
        request = {'access_token': token, 'partner_key': partner, 'elements_per_page': '4000'}
        data = json.loads(requests.get(mainURL+'families', params=request).text)
        return data
    def search(self, query, token):
        data = []
        request = {'access_token': token, 'query': query}
        json_data = json.loads(requests.get(mainURL+'search/', params=request).text)
        shows = []
        for element in json_data:
            if element['type'] == 'show':
                shows.append(str(element['id']))
        search = '%2C'.join(shows)
        request = {'access_token': token, 'id_show': search}
        data = json.loads(requests.get(mainURL+'shows/by_id/'+search, params=request).text)
        return data
    def get_last(self, partner, token, num_video):
        request = {'access_token': token, 'partner_key': partner, 'elements_per_page': num_video}
        data = json.loads(requests.get(mainURL+'shows/', params=request).text)

        if plugin.get_setting('showseen') == 'true':
            return data
        else:
            d = []
            for e in data:
                if e['mark_read'] == None:
                    d.append(e)
            return d
        return data
    def get_popular(self, partner, token, num_video):
        request = {'access_token': token, 'partner_key': partner, 'elements_per_page': num_video}
        data = json.loads(requests.get(mainURL+'shows/most_popular', params=request).text)
        if plugin.get_setting('showseen') == 'true':
            return data
        else:
            d = []
            for e in data:
                if e['mark_read'] == None:
                    d.append(e)
            return d
        return data
    def get_fambytype(self, partner, typename, token):
        request = {'access_token': token, 'partner_key': partner, 'type_key': typename, 'elements_per_page': '4000'}
        data = json.loads(requests.get(mainURL+'families', params=request).text)
        return data
    def get_families(self, partner, theme, token):
        request = {'access_token': token, 'partner_key': partner, 'theme_key': theme, 'elements_per_page': '4000'}
        data = json.loads(requests.get(mainURL+'families', params=request).text)
        return data
    def get_playlists(self, token):
        request = {'access_token': token}
        playlists = []
        data = json.loads(requests.get(mainURL+'users/queue_list', params=request).text)
        for p in data:
            playlists.append(p)
        return playlists
    def get_videodata(self, token, vid):
        request = {'access_token': token, 'id_show': vid}
        data = json.loads(requests.get(mainURL+'shows/by_id/'+vid, params=request).text)
        return data[0]
    def get_videos(self, partner, family, token, num_video):
        request = {'access_token': token, 'partner_key': partner, 'family_key': family, 'elements_per_page': num_video}
        data = json.loads(requests.get(mainURL+'shows', params=request).text)
        if plugin.get_setting('showseen') == 'true':
            return data
        else:
            d = []
            for e in data:
                if e['mark_read'] == None:
                    d.append(e)
            return d
    def get_random(self, partner, family, token, quality):
        request = {'access_token': token, 'partner_key': partner, 'family_key': family, 'elements_per_page': '4000'}
        data = json.loads(requests.get(mainURL+'shows', params=request).text)
        notseen = []
        for e in data:
            if e['mark_read'] == None:
                notseen.append(e)
        if len(notseen) > 0:
            r = randint(0, len(notseen))
            return str(notseen[r]['id_show'])
    def get_video(self, show, token, quality):
        show_lang = ''
        subs = None
        request = {'access_token': token, 'id_show': show}
        langs = json.loads(requests.get(mainURL+'shows/'+show+'/languages', params=request).text)
        for lang in langs:
            if plugin.get_setting('lang') == lang['audio_lang']:
                show_lang = lang['audio_lang']
                if lang['sub_lang'] != None:
                    subs = lang['sub_lang']
        if show_lang == '':
            show_lang = langs[0]['audio_lang']
            subs = langs[0]['sub_lang']
        request = {'access_token': token, 'sub_lang': subs}
        data = json.loads(requests.get(mainURL+'shows/'+show+'/video/'+quality+'/'+show_lang, params=request).text)
        return data['file']
    def __get_json(self, url, items=None):
        if items:
            request = urlencode(items)
            req = Request(url, request)
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            raise BaseException('HTTPError: %s' % error)
        except URLError, error:
            raise BaseException('URLError: %s' % error)
        json_data = json.loads(response)
        return json_data
