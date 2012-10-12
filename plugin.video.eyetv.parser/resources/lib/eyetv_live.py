#
# Copyright (C) 2012 Benjamin Bertrand
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# http://www.gnu.org/copyleft/gpl.html

import urllib2
import urlparse
import gzip
import time
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import simplejson as json
from xbmcswift import xbmc, xbmcgui
from config import plugin


EYETVPORT = 2170


class EyetvLive:
    """Class to watch live TV using EyeTV iPhone access"""

    def __init__(self, server, bitrate, password):
        """Initialization"""
        self.base_url = 'http://%s:%d' % (server, EYETVPORT)
        self.bitrate = bitrate
        self.username = 'eyetv'
        self.password = password
        if not self.is_up():
            xbmc.log('EyeTV is not running', xbmc.LOGERROR)
            xbmcgui.Dialog().ok(plugin.get_string(30110), plugin.get_string(30111))
            exit(0)
        if not self.wifi_access_is_on():
            xbmc.log('iPhone Access returned an error', xbmc.LOGERROR)
            xbmcgui.Dialog().ok(plugin.get_string(30110), plugin.get_string(30112))
            exit(0)

    def get_data(self, url):
        """Return the dictionary corresponding to the url request

        EyeTV server always returns  a dictionary encoded in JSON"""
        full_url = urlparse.urljoin(self.base_url, url)
        # Handle authentication
        authhandler = urllib2.HTTPDigestAuthHandler()
        authhandler.add_password("EyeTV Wi-Fi Access", self.base_url, self.username, self.password)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
        # Build request with proper header
        request = urllib2.Request(full_url)
        request.add_header('Accept-encoding', 'gzip')
        try:
            f = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            xbmc.log(str(e), xbmc.LOGERROR)
            if e.code == 401:
                xbmcgui.Dialog().ok(plugin.get_string(30110), plugin.get_string(30115))
            else:
                xbmcgui.Dialog().ok(plugin.get_string(30110), str(e))
            exit(0)
        except urllib2.URLError, e:
            xbmc.log('URLError: %s %s' % (full_url, str(e.reason)), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(plugin.get_string(30110), plugin.get_string(30114))
            exit(0)
        if f.headers.get('Content-Encoding') == 'gzip':
            compresseddata = f.read()
            gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(compresseddata))
            data = gzipper.read()
        else:
            data = f.read()
        xbmc.log(full_url, xbmc.LOGDEBUG)
        xbmc.log(str(data), xbmc.LOGDEBUG)
        if f.headers.get('Content-Type') == 'application/json':
            return json.loads(data)
        else:
            return data

    def get_key_from_data(self, key, url):
        """Return the value associated to key in the dictionay returned
        by the EyeTV server to the url request"""
        data = self.get_data(url)
        return data[key]

    def is_up(self):
        """Return True if EyeTV is up and running"""
        return self.get_key_from_data('isUp', 'live/status')

    def wifi_access_is_on(self):
        """Return True if EyeTV iPhone access is enabled"""
        return self.get_key_from_data('WifiAccesIsOn', 'live/seed')

    def get_channels(self):
        """Return the list of channels available in EyeTV (as a dictionary)"""
        return self.get_key_from_data('channelList', 'live/channels')

    def is_ready_to_stream(self):
        """Return True when EyeTV is ready to stream the chosen channel"""
        data = self.get_data('live/ready')
        xbmc.log('doneEncoding: %(doneEncoding)f, isReadyToStream: %(isReadyToStream)s' % data, xbmc.LOGDEBUG)
        return data['isReadyToStream']

    def get_channel_url(self, serviceid):
        """Return the m3u8 url of the channel to stream"""
        # "live/tuneto/1/"+this.connectionSpeed according to main.js (safari)
        # connectionSpeed is set to 320 when using safari
        # "live/tuneto/6/800/0/1/6/" with eyeTV app on iPhone
        # "live/tuneto/6/1200/0/1/6/" with eyeTV app on iPad
        # We pass the bitrate set in the preferences
        data = self.get_data('/'.join(('live/tuneto/1', self.bitrate, serviceid)))
        if not data['success']:
            xbmc.log('live/tuneto error code: %d' % data['errorcode'], xbmc.LOGERROR)
            xbmcgui.Dialog().ok(plugin.get_string(30110), plugin.get_string(30113))
            exit(0)
        # Wait before checking if stream is ready
        # Otherwise we get the answer for the old stream when changing channel
        time.sleep(1)
        while (not self.is_ready_to_stream()):
                time.sleep(1)
        return '/'.join((self.base_url, 'live/stream', data['m3u8URL']))
