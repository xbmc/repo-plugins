"""
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
"""

import gzip
import json
import re
import ssl
import urllib.request
import urllib.parse
import urllib.error
import xbmc
import xbmcvfs
from io import BytesIO

CERT_FILE = xbmcvfs.translatePath('special://xbmc/system/certs/cacert.pem')


def request(url, headers=None, params=None, timeout='20'):
    _headers = {}
    if headers:
        _headers.update(headers)

    handlers = []
    ssl_context = ssl.create_default_context(cafile=CERT_FILE)
    ssl_context.set_alpn_protocols(['http/1.1'])
    handlers += [urllib.request.HTTPSHandler(context=ssl_context)]
    opener = urllib.request.build_opener(*handlers)
    opener = urllib.request.install_opener(opener)

    if 'User-Agent' in _headers:
        pass
    else:
        _headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'

    if params is not None:
        if isinstance(params, dict):
            params = urllib.parse.urlencode(params)
        url = url + '?' + params

    if 'Accept-Language' not in _headers:
        _headers['Accept-Language'] = 'en-US,en'

    if 'Accept-Encoding' in _headers:
        pass
    else:
        _headers['Accept-Encoding'] = 'gzip'

    req = urllib.request.Request(url)
    _add_request_header(req, _headers)

    try:
        response = urllib.request.urlopen(req, timeout=int(timeout))
    except urllib.error.URLError:
        return ''
    except urllib.error.HTTPError:
        return ''

    result = response.read()
    encoding = None

    if response.headers.get('content-encoding', '').lower() == 'gzip':
        result = gzip.GzipFile(fileobj=BytesIO(result)).read()

    content_type = response.headers.get('content-type', '').lower()

    if 'charset=' in content_type:
        encoding = content_type.split('charset=')[-1]

    if encoding is None:
        epatterns = [r'<meta\s+http-equiv="Content-Type"\s+content="(?:.+?);\s+charset=(.+?)"',
                     r'xml\s*version.+encoding="([^"]+)']
        for epattern in epatterns:
            epattern = epattern.encode('utf8')
            r = re.search(epattern, result, re.IGNORECASE)
            if r:
                encoding = r.group(1).decode('utf8')
                break

    if encoding is not None:
        result = result.decode(encoding, errors='ignore')
    elif 'json' in content_type:
        result = json.loads(result.decode('utf-8'))
    else:
        xbmc.log('Unknown Page Encoding', xbmc.LOGDEBUG)

    response.close()
    return result


def _add_request_header(_request, headers):
    try:
        scheme = urllib.parse.urlparse(_request.get_full_url()).scheme
        host = _request.host
        referer = headers.get('Referer', '') or '%s://%s/' % (scheme, host)
        _request.add_unredirected_header('Host', host)
        _request.add_unredirected_header('Referer', referer)
        for key in headers:
            _request.add_header(key, headers[key])
    except BaseException:
        return
