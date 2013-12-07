#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
# https://docs.google.com/document/d/1_rs5BXklnLqGS6g6eAjevVHsPafv4PXDCi_dAM2b7G0/edit?pli=1
#
import urllib
import urllib2
import re

import xbmc

try:
    import json
except:
    import simplejson as json

API_URL = 'http://api.yousee.tv/rest'
API_KEY = 'HCN2BMuByjWnrBF4rUncEfFBMXDumku7nfT3CMnn'

AREA_LIVETV = 'livetv'
AREA_MOVIE = 'movie'
AREA_PLAY = 'play'
AREA_USERS = 'users'
AREA_TVGUIDE = 'tvguide'
AREA_SYSTEM = 'system'
AREA_CONTENT = 'content'
AREA_ARCHIVE = 'archive'

METHOD_GET = 'get'
METHOD_POST = 'post'


class YouSeeApiException(Exception):
    pass


class YouSeeApi(object):
    def _invoke(self, area, function, params=None, method=METHOD_GET):
        url = API_URL + '/' + area + '/' + function
        if method == METHOD_GET and params:
            for key, value in params.items():
                url += '/' + key + '/' + str(value)
        url += '/format/json'

        xbmc.log('Invoking URL: %s' % re.sub('/password/([^/]+)/', '/password/****/', url), xbmc.LOGDEBUG)

        try:
            r = urllib2.Request(url, headers={'X-API-KEY': API_KEY})
            if method == METHOD_POST and params:
                xbmc.log("POST data: %s" % urllib.urlencode(params), xbmc.LOGDEBUG)
                r.add_data(urllib.urlencode(params))
            u = urllib2.urlopen(r)
            data = u.read()
            u.close()
        except urllib2.HTTPError, error:
            data = error.read()
        except Exception, ex:
            raise YouSeeApiException(ex)

        try:
            return json.loads(data)
        except:
            return None


class YouSeeLiveTVApi(YouSeeApi):
    def channel(self, id):
        """
        Returns metadata for channel based on channel id.

        @param id: channel id
        @return:
        """
        return self._invoke(AREA_LIVETV, 'channel', {
            'id': id
        })

    def popularChannels(self):
        """
        Returns list of channels sorted by popularity.
        Based on live viewing data from yousee.tv
        """
        return self._invoke(AREA_LIVETV, 'popularchannels')

    def allowedChannels(self):
        """
        Returns list of channels the requesting IP is allowed to stream.
        """
        return self._invoke(AREA_LIVETV, 'allowed_channels', {
            'apiversion': 2
        })

    def suggestedChannels(self):
        """
        Returns list of channels that should be presented to the user. NOTE: this is not the list of allowed channels.
        A non-yousee bredbaand user will get a list of channels from "Grundpakken".
        """
        return self._invoke(AREA_LIVETV, 'suggested_channels')

    def streamUrl(self, channelId, client='xbmc'):
        """
        Returns absolute streaming URL for channel.
        Channel rights are based on client ip address.

        @param channelId: Unique ID of channel (e.g. 1 for DR1)
        @type channelId: int
        @param client: client identifier. Handset or platform. Used to determine best stream.
        @type client: str
        """
        json = self._invoke(AREA_LIVETV, 'streamurl', {
            'channel_id': channelId,
            'client': client
        })

        return json


class YouSeeUsersApi(YouSeeApi):
    def isYouSeeIP(self):
        return self._invoke(AREA_USERS, 'isyouseeip')
