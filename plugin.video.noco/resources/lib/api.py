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
import httplib
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

def correctByIdOrder(data, order, key):
    '''
    Reorder list returned by request of type */by_id/id1,id2,...
    as it seems to be reordered by ascending id
    and not ordered in the given input id list order (which is sometimes required)
    '''
    if not len(order):
        return []
    # Create a dictionary with id value as only key
    data_dict = {int(item[key]):item for item in data}
    # Now create the ordered list (need a loop to test id that exist in the input list but not existing in the list returned by_id)
    ret = []
    for id_val in order:
        key_val = int(id_val) 
        if key_val in data_dict:
            ret.append(data_dict[key_val])
    return ret

class nocoApi():
    def get_token(self, user, password):
        requestHandler = build_opener()
        r = requests.post(mainURL+"OAuth2/authorize.php?response_type=code&client_id="+client_id+"&state=STATE", allow_redirects=False, data = {'username': user,'password': password,'login': '1'})
        ts = time.time()
        code = parse_qs(urlparse(r.headers['location']).query)['code'][0]
        apirequest = urlencode({'grant_type': 'authorization_code',
                                'code': code})
        requestHandler = build_opener()
        requestHandler.addheaders = [('Authorization', b'Basic ' + b64encode(client_id + b':' + client_secret))]
        token = requestHandler.open(mainURL+"OAuth2/token.php", apirequest).read()
        data = json.loads(token)
        expire = time.time() + float(data['expires_in'])
        return str(data['access_token']), expire, str(data['refresh_token'])
    def get_guest_token(self):
        apirequest = urlencode({'grant_type': 'client_credentials'})
        requestHandler = build_opener()
        requestHandler.addheaders = [('Authorization', b'Basic ' + b64encode(client_id + b':' + client_secret))]
        token = requestHandler.open(mainURL+"OAuth2/token.php", apirequest).read()
        data = json.loads(token)
        expire = time.time() + float(data['expires_in'])
        return str(data['access_token']), expire
    def renew_token(self, renew):
        apirequest = urlencode({'grant_type': 'refresh_token',
                                'refresh_token': renew})
        requestHandler = build_opener()
        requestHandler.addheaders = [('Authorization', b'Basic ' + b64encode(client_id + b':' + client_secret))]
        token = requestHandler.open(mainURL+"OAuth2/token.php", apirequest).read()
        data = json.loads(token)
        expire = time.time() + float(data['expires_in'])
        return str(data['access_token']), str(expire), str(data['refresh_token'])

    def get_subscribed_partners(self, token):
        partners = []
        request = {'access_token': token}
        data = json.loads(requests.get(mainURL+'partners/subscribed', params=request).text)
        for element in data:
            if not element['nb_shows'] == None:
               partners.append(element) 
        return partners
    # guest partners = all partners with at least 1 guest free show available
    def get_guest_partners(self, token):
        partners = []
        request = {'access_token': token}
        data = json.loads(requests.get(mainURL+'partners', params=request).text)
        for element in data:
            if not element['nb_shows'] == None:
                dummy, last = self.get_last(element['partner_key'], token, elements_per_page=1, page=0, guest_free=True)
                if len(last):
                    partners.append(element) 
        return partners
    # user free partners = (all partners - subscribed partners) with at least 1 user free show available
    def get_user_free_partners(self, token):
        partners = []
        subscribed_partners = self.get_subscribed_partners(token)
        subscribed_ids = [p['id_partner'] for p in subscribed_partners]
        request = {'access_token': token}
        all_partners = json.loads(requests.get(mainURL+'partners', params=request).text)
        for element in all_partners:
            if not element['nb_shows'] == None and not element['id_partner'] in subscribed_ids:
                dummy, last = self.get_last(element['partner_key'], token, elements_per_page=1, page=0, user_free=True)
                if len(last):
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
    def search(self, query, token, elements_per_page, page):
        data = []
        request = {'access_token': token, 'query': query, 'elements_per_page': elements_per_page, 'page': page}
        try:
            json_data = json.loads(requests.get(mainURL+'search/', params=request).text)
        except ValueError, e:
            return False, []
        hasNextPage = False if len(json_data) < elements_per_page else True
        shows = []
        for element in json_data:
            if element['type'] == 'show':
                shows.append(str(element['id']))
        search = '%2C'.join(shows)
        request = {'access_token': token, 'id_show': search}
        data = json.loads(requests.get(mainURL+'shows/by_id/'+search, params=request).text)
        return hasNextPage, correctByIdOrder(data, order=shows, key='id_show')
    def get_last(self, partner, token, elements_per_page=40, page=0, guest_free=False, user_free=False):
        request = {'access_token': token,
                   'partner_key': partner,
                   'mark_read': None if plugin.get_setting('showseen') == 'true' else '0',
                   'guest_free': None if not guest_free else '1',
                   'user_free': None if not user_free else '1',
                   'elements_per_page': elements_per_page,
                   'page': page}
        data = json.loads(requests.get(mainURL+'shows/', params=request).text)
        hasNextPage = False if len(data) < elements_per_page else True
        return hasNextPage, data
    def get_popular(self, partner, token, elements_per_page, page, period):
        request = {'access_token': token,
                   'partner_key': partner,
                   'mark_read': None if plugin.get_setting('showseen') == 'true' else '0',
                   'period': period,
                   'elements_per_page': elements_per_page,
                   'page': page}
        data = json.loads(requests.get(mainURL+'shows/most_popular', params=request).text)
        hasNextPage = False if len(data) < elements_per_page else True
        return hasNextPage, data
    def get_toprated(self, partner, token, elements_per_page, page, period):
        request = {'access_token': token,
                   'partner_key': partner,
                   'mark_read': None if plugin.get_setting('showseen') == 'true' else '0',
                   'period': period,
                   'elements_per_page': elements_per_page,
                   'page': page}
        data = json.loads(requests.get(mainURL+'shows/top_rated', params=request).text)
        hasNextPage = False if len(data) < elements_per_page else True
        return hasNextPage, data
    def get_history(self, token, elements_per_page, page):
        request = {'access_token': token, 'elements_per_page': elements_per_page, 'page': page}
        json_data = json.loads(requests.get(mainURL+'users/history', params=request).text)
        hasNextPage = False if len(json_data) < elements_per_page else True
        shows = []
        for element in json_data:
            shows.append(str(element['id_show']))
        history = '%2C'.join(shows)
        request = {'access_token': token}
        data = json.loads(requests.get(mainURL+'shows/by_id/'+history, params=request).text)
        return hasNextPage, correctByIdOrder(data, order=shows, key='id_show')
    def get_fambytype(self, partner, typename, token):
        request = {'access_token': token, 'partner_key': partner, 'type_key': typename, 'elements_per_page': '4000'}
        data = json.loads(requests.get(mainURL+'families', params=request).text)
        return data
    def get_fambyids(self, token, fids):
        request = {'access_token': token}
        data = json.loads(requests.get(mainURL+'families/by_id/'+'%2C'.join(str(fids)[1:-1].replace(' ','').split(',')), params=request).text)
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
    def set_playlist(self, token, playlist):
        if not len(playlist):
            self.clear_playlist(token)
            return          
        urlparsed = urlparse(mainURL)
        connection = httplib.HTTPSConnection(urlparsed.netloc)
        headers = { 'Authorization': 'Bearer '+ token, 'Content-Type': 'application/x-www-form-urlencoded'}
        connection.request("PUT", urlparsed.path + "users/queue_list", str(playlist), headers)
        response = connection.getresponse()
        data = json.loads(response.read())
    def clear_playlist(self, token):
        request = {'access_token': token}
        requests.delete(mainURL+'users/queue_list', params=request)
        return
    def get_favorites(self, token):
        request = {'access_token': token}
        favorites = []
        data = json.loads(requests.get(mainURL+'users/favorites', params=request).text)
        return data[0]
    def set_favorite(self, token, favorite):
        if not len(favorite):
            self.clear_favorite(token)
            return          
        urlparsed = urlparse(mainURL)
        connection = httplib.HTTPSConnection(urlparsed.netloc)
        headers = { 'Authorization': 'Bearer '+ token, 'Content-Type': 'application/x-www-form-urlencoded'}
        connection.request("PUT", urlparsed.path + "users/favorites", str(favorite), headers)
        response = connection.getresponse()
        return
    def clear_favorite(self, token):
        request = {'access_token': token}
        requests.delete(mainURL+'users/favorites', params=request)
        return
    def get_videodata(self, token, vids):
        request = {'access_token': token}
        data = json.loads(requests.get(mainURL+'shows/by_id/'+'%2C'.join(str(vids)[1:-1].replace(' ','').split(',')), params=request).text)
        return correctByIdOrder(data, order=vids, key='id_show')
    def get_videos(self, partner, family, token, elements_per_page, page):
        request = {'access_token': token, 'partner_key': partner, 'family_key': family, 'mark_read': None if plugin.get_setting('showseen') == 'true' else '0', 'elements_per_page': elements_per_page, 'page': page}
        data = json.loads(requests.get(mainURL+'shows', params=request).text)
        hasNextPage = False if len(data) < elements_per_page else True
        return hasNextPage, data
    def get_random(self, partner, family, token, quality):
        request = {'access_token': token, 'partner_key': partner, 'family_key': family, 'mark_read': None if plugin.get_setting('showseen') == 'true' else '0', 'elements_per_page': '40'}
        data = json.loads(requests.get(mainURL+'shows/rand', params=request).text)
        if not len(data):
            return None
        return [item['rating_fr'] for item in data] , [str(item['id_show']) for item in data]
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
    def set_rating(self, token, show, rating):
        request = {'access_token': token}
        requests.post(mainURL+"shows/"+show+"/rate/"+str(rating), params=request)
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
