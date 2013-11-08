'''
    RockPeaks plugin for XBMC
    Copyright 2013 Artem Matsak

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import urllib
import urllib2
if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json

class RockPeaksAPI():
    APIKEY = 'c9358b19a1fde1c7cdbc7cf492a541c7'
    endpoint = 'http://www.rockpeaks.com/services/api'

    def request(self, method, params):
        default_params = {
            'method': method,
            'api_key': self.APIKEY,
            'format': 'json'
        }
        params = dict(params.items() + default_params.items())

        try:
            con = urllib2.urlopen(self.endpoint + '?' + urllib.urlencode(params))
            inputdata = con.read()
            ret_obj = _json.loads(inputdata)
            con.close()
            return ret_obj

        except urllib2.HTTPError, e:
            return {}
