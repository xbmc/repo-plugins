# -*- coding: utf-8 -*-
'''
Created on Sep 9, 2010
@author: Zsolt Török, Vanhoutteghem Pieter

Copyright (C) 2010 Zsolt Török
 
This file is part of XBMC SoundCloud Plugin.

XBMC SoundCloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

XBMC SoundCloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with XBMC SoundCloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''
import sys
import httplib2
import urllib
import simplejson as json
import urlparse

# SoundCloud application consumer key.
CONSUMER_KEY = "hijuflqxoOqzLdtr6W4NA"
CLIENT_ID_VALUE = CONSUMER_KEY
REDURI = "plugin://plugin.audio.soundcloud/oauth_callback"
LOGINURL = "https://soundcloud.com/connect/login"

GRANT_TYPE_PASSWORD_VALUE = u'password'
GRANT_TYPE_REFRESH_TOKEN_VALUE = u'refresh_token'
CLIENT_ID_KEY = u'client_id'
CLIENT_SECRET_KEY = u'client_secret'
GRANT_TYPE_KEY = u'grant_type'
SCOPE = u'scope'
NONE_EXPIRY = "non-expiring"
USERNAME_KEY = u'username'
PASSWORD_KEY = u'password'
RESPONSETYPE = u'response_type'
TOKEN = "token"
REDIRECTURI = u'redirect_uri'
DISPLAY = u'display'
POPUP = "popup"

# SoundCloud constants
USER_AVATAR_URL = 'avatar_url'
USER_PERMALINK = 'permalink'
USER_ID = 'id'
USER_NAME = 'username'
USER_PERMALINK_URL = 'permalink_url'
TRACK_USER = 'user'
TRACK_TITLE = 'title'
TRACK_ARTWORK_URL = 'artwork_url'
TRACK_WAVEFORM_URL = 'waveform_url'
TRACK_STREAM_URL = 'stream_url'
TRACK_STREAMABLE = 'streamable'
TRACK_GENRE = 'genre'
TRACK_ID = 'id'
TRACK_PERMALINK = 'permalink'
GROUP_ARTWORK_URL = 'artwork_url'
GROUP_NAME = 'name'
GROUP_ID = 'id'
GROUP_CREATOR = 'creator'
GROUP_PERMALINK_URL = 'permalink_url'
GROUP_PERMALINK = 'permalink'
QUERY_CONSUMER_KEY = 'consumer_key'
QUERY_FILTER = 'filter'
QUERY_OFFSET = 'offset'
QUERY_LIMIT = 'limit'
QUERY_Q = 'q'
QUERY_ORDER = 'order'
QUERY_OAUTH_TOKEN = 'oauth_token'
QUERY_CURSOR = 'cursor'

class SoundCloudClient(object):
    ''' SoundCloud client to handle all communication with the SoundCloud REST API. '''

    def __init__(self, login=False, username='', password='', oauth_token=''):
        '''
        Constructor
        '''
        self.login = login
        self.username = username
        self.password = password
        if login:
            if oauth_token:
                self.oauth_token = oauth_token
            else:
                self.oauth_token = self.get_oauth_tokens(LOGINURL)
        
    def get_oauth_tokens(self, url):
        try:
            oauth_access_token = self.getlogintoken(url)
        except:
            oauth_access_token = ""
            self.login = False
        return oauth_access_token
    
    def getlogintoken(self,url):
        #https://soundcloud.com/connect/login
        #params =
        #<form id="oauth2-login-form" class="authorize-client log-in existing-user authorize-token throbberform" method="post" action="/connect/login">
        #<input id="client_id" type="hidden" value="91c61ef4dbc96933eff93325b5d5183e" name="client_id">
        #<input id="redirect_uri" type="hidden" value=""plugin://plugin.audio.soundcloud/oauth_callback"" name="redirect_uri">
        #<input id="response_type" type="hidden" value="token" name="response_type">
        #<input id="scope" type="hidden" value="non-expiring" name="scope">
        #<input id="display" type="hidden" value="popup" name="display">
        #<input id="username" class="title" type="text" name="username" maxlength="255">
        #<input id="password" class="title" type="password" name="password">

        urlparams = {CLIENT_ID_KEY: CLIENT_ID_VALUE,
                   REDIRECTURI: REDURI,
                   RESPONSETYPE: TOKEN,
                   SCOPE: NONE_EXPIRY,
                   DISPLAY: POPUP,
                   USERNAME_KEY: self.username,
                   PASSWORD_KEY: self.password}
        urldata = urllib.urlencode(urlparams)
        h = httplib2.Http(disable_ssl_certificate_validation=True)
        response, content = h.request(url, 'POST', urldata,
                                         headers={'Content-type': 'application/x-www-form-urlencoded'})

        qs = dict(urlparse.parse_qs(response['location']))
        return qs.get(REDURI + "?#access_token")[0]

#AUTHENTICATED ACCESS

    def get_favorite_tracks(self, offset, limit, mode, plugin_url):
        ''' Return a list of tracks favorited by the current user, based on the specified parameters.  login only'''
        url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/favorites", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def get_own_tracks(self, offset, limit, mode, plugin_url):
        ''' Return a list of tracks favorited by the current user, based on the specified parameters.  login only'''
        url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/tracks", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)
           
    def get_dash_tracks(self, limit, mode, plugin_url, cursor):
        ''' Return a list of new tracks by the following users of the current user, based on the specified parameters.  login only'''
        if cursor == "":
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/affiliated", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        else:
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/affiliated", parameters={ QUERY_CURSOR: cursor, QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        return self._get_activities_tracks(url)
    
    def get_private_tracks(self, limit, mode, plugin_url, cursor):
        ''' Return a list of tracks privately shared to the current user, based on the specified parameters.  login only'''
        if cursor == "":
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/exclusive", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        else:
            url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/activities/tracks/exclusive", parameters={ QUERY_CURSOR: cursor, QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_LIMIT: limit})
        return self._get_activities_tracks(url)
    
    def _get_activities_tracks(self, url):
        json_content = self._http_get_json(url)
        tracks = []
        for json_entry in json_content["collection"]:
            try:
                track_entry = json_entry["origin"]
                if TRACK_ARTWORK_URL in track_entry and track_entry[TRACK_ARTWORK_URL]:
                    thumbnail_url = track_entry[TRACK_ARTWORK_URL]
                else:
                    thumbnail_url = track_entry[TRACK_USER].get(USER_AVATAR_URL)
                tracks.append({ TRACK_TITLE: track_entry[TRACK_TITLE], TRACK_STREAM_URL: track_entry.get(TRACK_STREAM_URL, ""), TRACK_ARTWORK_URL: thumbnail_url, TRACK_PERMALINK: track_entry[TRACK_PERMALINK], TRACK_ID: track_entry[TRACK_ID] })
            except:
                print(track_entry)
            
        try:
            qs = dict(urlparse.parse_qs(urlparse.urlparse(json_content["next_href"]).query))
            nexturl = qs.get(QUERY_CURSOR)[0]
        except:
            nexturl = ""
            
        return tracks,nexturl

    def get_following_groups(self, offset, limit, mode, plugin_url):
        url = self._build_query_url(base='https://api.soundcloud.com/', resource_type="me/groups", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_groups(url)
    
    def get_following_users(self, offset, limit, mode, plugin_url):
        url = self._build_query_url(base="https://api.soundcloud.com/", resource_type="me/followings", parameters={ QUERY_OAUTH_TOKEN: self.oauth_token, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_users(url)
        
    def get_follower_users(self, offset, limit, mode, plugin_url):
        url = self._build_query_url(base="https://api.soundcloud.com/", resource_type="me/followers", parameters={ QUERY_OAUTH_TOKEN : self.oauth_token, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_users(url)


#NORMAL ACCESS        
    
    def get_tracks(self, offset, limit, mode, plugin_url, query=""):
        ''' Return a list of tracks from SoundCloud, based on the parameters. '''
        if query == "":
            url = self._build_query_url(base="http://api.soundcloud.com/", resource_type="tracks", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        else:
            url = self._build_query_url(base="http://api.soundcloud.com/", resource_type="tracks", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def get_group_tracks(self, offset, limit, mode, plugin_url, group_id):
        ''' Return a list of tracks belonging to the given group, based on the specified parameters. '''
        url = self._build_groups_query_url(base='http://api.soundcloud.com/', resource_type="tracks", group_id=group_id, parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def get_user_tracks(self, offset, limit, mode, plugin_url, user_permalink):
        ''' Return a list of tracks uploaded by the given user, based on the specified parameters. '''
        url = self._build_users_query_url(base='http://api.soundcloud.com/', resource_type="tracks", user_permalink=user_permalink, parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def get_normal_groups(self, offset, limit, mode, plugin_url, query=""):
        ''' Return a list of groups, based on the specified parameters. '''
        url = self._build_query_url(base='http://api.soundcloud.com/', resource_type="groups", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_groups(url)
            
    def get_users(self, offset, limit, mode, plugin_url, query=""):
        url = self._build_query_url(base='http://api.soundcloud.com/', resource_type="users", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        return self._get_users(url)

    def _get_groups(self, url):
        ''' Return a list of groups'''    
        json_content = self._http_get_json(url)    
        groups = []
        for json_entry in json_content:
            if GROUP_ARTWORK_URL in json_entry and json_entry[GROUP_ARTWORK_URL]:
                thumbnail_url = json_entry[GROUP_ARTWORK_URL]
            elif GROUP_CREATOR in json_entry and json_entry[GROUP_CREATOR] and USER_AVATAR_URL in json_entry[GROUP_CREATOR] and json_entry[GROUP_CREATOR][USER_AVATAR_URL]:
                thumbnail_url = json_entry[GROUP_CREATOR][USER_AVATAR_URL]
            else:
                thumbnail_url = ""
            groups.append({ GROUP_NAME: json_entry[GROUP_NAME], GROUP_ARTWORK_URL: thumbnail_url, GROUP_ID: json_entry[GROUP_ID], GROUP_PERMALINK_URL: json_entry[GROUP_PERMALINK_URL], GROUP_PERMALINK: json_entry[GROUP_PERMALINK] })

        return groups

    def _get_tracks(self, url):
        ''' Return a list of tracks'''
        json_content = self._http_get_json(url)
        tracks = []
        for json_entry in json_content:
            if TRACK_ARTWORK_URL in json_entry and json_entry[TRACK_ARTWORK_URL]:
                thumbnail_url = json_entry[TRACK_ARTWORK_URL]
            else:
                thumbnail_url = json_entry[TRACK_USER].get(USER_AVATAR_URL)
            tracks.append({ TRACK_TITLE: json_entry[TRACK_TITLE], TRACK_STREAM_URL: json_entry.get(TRACK_STREAM_URL, ""), TRACK_ARTWORK_URL: thumbnail_url, TRACK_PERMALINK: json_entry[TRACK_PERMALINK], TRACK_ID: json_entry[TRACK_ID] })

        return tracks

    def _get_users(self, url):
        ''' Return a list of users'''
        json_content = self._http_get_json(url)
        users = []
        for json_entry in json_content:
            users.append({ USER_NAME: json_entry[USER_NAME], USER_AVATAR_URL: json_entry[USER_AVATAR_URL], USER_ID: json_entry[USER_ID], USER_PERMALINK_URL: json_entry[USER_PERMALINK_URL], USER_PERMALINK: json_entry[USER_PERMALINK] })

        return users

    def get_track(self, id):
        ''' Return a track from SoundCloud based on the id. '''
        url = self._build_track_query_url(id, base='http://api.soundcloud.com/', parameters={QUERY_CONSUMER_KEY: CONSUMER_KEY})
        json_content = self._http_get_json(url)

        if TRACK_ARTWORK_URL in json_content and json_content[TRACK_ARTWORK_URL]:
                thumbnail_url = json_content[TRACK_ARTWORK_URL]
        else:
                thumbnail_url = json_content[TRACK_USER].get(USER_AVATAR_URL)

        track_stream_url = '%s?%s' % (json_content[TRACK_STREAM_URL], str(urllib.urlencode({QUERY_CONSUMER_KEY: CONSUMER_KEY})))
        return { TRACK_STREAM_URL: track_stream_url, TRACK_TITLE: json_content[TRACK_TITLE], TRACK_ARTWORK_URL: thumbnail_url, TRACK_GENRE: json_content[TRACK_GENRE] }

    def _build_query_url(self, resource_type, parameters, base="http://api.soundcloud.com/", format="json"):
        url = '%s%s.%s?%s' % (base, resource_type, format, str(urllib.urlencode(parameters)))
        return url

    def _build_track_query_url(self, permalink, parameters, base="http://api.soundcloud.com/", format="json"):
        url = '%stracks/%s.%s?%s' % (base, permalink, format, str(urllib.urlencode(parameters)))
        return url

    def _build_groups_query_url(self, group_id, resource_type, parameters, base="http://api.soundcloud.com/", format="json"):
        url = '%sgroups/%d/%s.%s?%s' % (base, group_id, resource_type, format, str(urllib.urlencode(parameters)))
        return url

    def _build_users_query_url(self, user_permalink, resource_type, parameters, base="http://api.soundcloud.com/", format="json"):
        url = '%susers/%s/%s.%s?%s' % (base, user_permalink, resource_type, format, str(urllib.urlencode(parameters)))
        return url
    
    def _http_get_json(self, url):
        h = httplib2.Http(disable_ssl_certificate_validation=True)
        resp, content = h.request(url, 'GET')
        if resp.status == 401:
            raise RuntimeError('Authentication error')
        
        return json.loads(content)
