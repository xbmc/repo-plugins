# -*- coding: utf-8 -*-
'''
Created on Sep 9, 2010
@author: Zsolt Török

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
import httplib2
import urllib
import simplejson as json

# SoundCloud application consumer key.
CONSUMER_KEY = "hijuflqxoOqzLdtr6W4NA"

# SoundCloud constants
USER_AVATAR_URL = u'avatar_url'
USER_PERMALINK = u'permalink'
USER_ID = u'id'
USER_NAME = u'username'
USER_PERMALINK_URL = u'permalink_url'
TRACK_USER = u'user'
TRACK_TITLE = u'title'
TRACK_ARTWORK_URL = u'artwork_url'
TRACK_WAVEFORM_URL = u'waveform_url'
TRACK_STREAM_URL = u'stream_url'
TRACK_STREAMABLE = u'streamable'
TRACK_GENRE = u'genre'
TRACK_ID = u'id'
TRACK_PERMALINK = u'permalink'
GROUP_ARTWORK_URL = u'artwork_url'
GROUP_NAME = u'name'
GROUP_ID = u'id'
GROUP_CREATOR = u'creator'
GROUP_PERMALINK_URL = u'permalink_url'
GROUP_PERMALINK = u'permalink'
QUERY_CONSUMER_KEY = u'consumer_key'
QUERY_FILTER = u'filter'
QUERY_OFFSET = u'offset'
QUERY_LIMIT = u'limit'
QUERY_Q = u'q'
QUERY_ORDER = u'order'

class SoundCloudClient(object):
    ''' SoundCloud client to handle all comminucation with the SoundCloud REST API. '''

    def __init__(self):
        '''
        Constructor
        '''
        print 'SCC init'

    def get_tracks(self, offset, limit, mode, plugin_url, query=""):
        ''' Return a list of tracks from SoundCloud, based on the parameters. '''
        url = self.build_query_url(resource_type="tracks", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        print "URL: " + url
        return self._get_tracks(url)

    def _get_tracks(self, url):
        h = httplib2.Http()
        resp, content = h.request(url, 'GET')
        json_content = json.loads(content)

        tracks = []
        for json_entry in json_content:
            if TRACK_ARTWORK_URL in json_entry and json_entry[TRACK_ARTWORK_URL]:
                thumbnail_url = json_entry[TRACK_ARTWORK_URL]
            else:
                thumbnail_url = json_entry[TRACK_USER].get(USER_AVATAR_URL)
            tracks.append({ TRACK_TITLE: json_entry[TRACK_TITLE], TRACK_STREAM_URL: json_entry.get(TRACK_STREAM_URL, ""), TRACK_ARTWORK_URL: thumbnail_url, TRACK_PERMALINK: json_entry[TRACK_PERMALINK] })

        return tracks

    def get_track(self, permalink):
        ''' Return a track from SoundCloud based on the permalink. '''
        url = self.build_track_query_url(permalink)
        h = httplib2.Http()
        resp, content = h.request(url, 'GET')
        json_content = json.loads(content)
        if TRACK_ARTWORK_URL in json_content and json_content[TRACK_ARTWORK_URL]:
                thumbnail_url = json_content[TRACK_ARTWORK_URL]
        else:
                thumbnail_url = json_content[TRACK_USER].get(USER_AVATAR_URL)
        return { TRACK_STREAM_URL: json_content[TRACK_STREAM_URL], TRACK_TITLE: json_content[TRACK_TITLE], TRACK_ARTWORK_URL: thumbnail_url, TRACK_GENRE: json_content[TRACK_GENRE] }

    def get_group_tracks(self, offset, limit, mode, plugin_url, group_id):
        ''' Return a list of tracks belonging to the given group, based on the specified parameters. '''
        url = self.build_groups_query_url(resource_type="tracks", group_id=group_id, parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def get_user_tracks(self, offset, limit, mode, plugin_url, user_permalink):
        ''' Return a list of tracks uploaded by the given user, based on the specified parameters. '''
        url = self.build_users_query_url(resource_type="tracks", user_permalink=user_permalink, parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_FILTER: TRACK_STREAMABLE, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_ORDER: "hotness"})
        return self._get_tracks(url)

    def get_groups(self, offset, limit, mode, plugin_url, query=""):
        ''' Return a list of groups, based on the specified parameters. '''
        h = httplib2.Http()
        url = self.build_query_url(resource_type="groups", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        resp, content = h.request(url, 'GET')
        json_content = json.loads(content)

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

    def get_users(self, offset, limit, mode, plugin_url, query=""):
        ''' Return a list of users, based on the specified parameters. '''
        h = httplib2.Http()
        url = self.build_query_url(resource_type="users", parameters={ QUERY_CONSUMER_KEY: CONSUMER_KEY, QUERY_OFFSET: offset, QUERY_LIMIT: limit, QUERY_Q: query, QUERY_ORDER: "hotness"})
        resp, content = h.request(url, 'GET')
        json_content = json.loads(content)

        users = []
        for json_entry in json_content:
            users.append({ USER_NAME: json_entry[USER_NAME], USER_AVATAR_URL: json_entry[USER_AVATAR_URL], USER_ID: json_entry[USER_ID], USER_PERMALINK_URL: json_entry[USER_PERMALINK_URL], USER_PERMALINK: json_entry[USER_PERMALINK] })

        return users

    def build_query_url(self, resource_type, parameters, base="http://api.soundcloud.com/", format="json"):
        url = '%s%s.%s?%s' % (base, resource_type, format, str(urllib.urlencode(parameters)))
        return url

    def build_track_query_url(self, permalink, base="http://api.soundcloud.com/", format="json"):
        url = '%stracks/%s.%s' % (base, permalink, format)
        return url

    def build_groups_query_url(self, group_id, resource_type, parameters, base="http://api.soundcloud.com/", format="json"):
        url = '%sgroups/%d/%s.%s?%s' % (base, group_id, resource_type, format, str(urllib.urlencode(parameters)))
        return url

    def build_users_query_url(self, user_permalink, resource_type, parameters, base="http://api.soundcloud.com/", format="json"):
        url = '%susers/%s/%s.%s?%s' % (base, user_permalink, resource_type, format, str(urllib.urlencode(parameters)))
        return url

