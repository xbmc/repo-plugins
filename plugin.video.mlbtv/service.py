# coding=UTF-8
# SPDX-License-Identifier: GPL-2.0-or-later
# Original proxy.plugin.example © matthuisman
# Modified for MLB.TV compatibility

import threading

import xbmc
import requests
import urllib

if sys.version_info[0] > 2:
    urllib = urllib.parse

try:
    # Python3
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.parse import urljoin
    from urllib.parse import urlparse
    from urllib.parse import parse_qs
except:
    # Python2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from urlparse import urljoin
    from urlparse import urlparse
    from urlparse import parse_qs

HOST = '127.0.0.1'
PORT = 43670
PROXY_URL = 'http://' + HOST + ':' + str(PORT) + '/'
STREAM_EXTENSION = '.m3u8'
URI_START_DELIMETER = 'URI="'
URI_END_DELIMETER = '"'
KEY_TEXT = '-KEY:METHOD=AES-128'
ENDLIST_TEXT = '#EXT-X-ENDLIST'
REMOVE_IN_HEADERS = ['upgrade', 'host']
REMOVE_OUT_HEADERS = ['date', 'server', 'transfer-encoding', 'keep-alive', 'connection', 'content-length', 'content-range', 'content-md5', 'access-control-allow-credentials', 'content-encoding']

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_POST(self):
        self.send_error(404)

    def do_HEAD(self):
        self.send_error(404)

    def do_GET(self):
        # parse path of the incoming request into components
        parsed_url = urlparse(self.path.lstrip('/').strip('\\'))
        # build our outgoing request URL without the querystring parameters
        url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path
        if not url.endswith(STREAM_EXTENSION):
            self.send_error(404)

        headers = {}
        pad = 0
        alternate_english = None
        alternate_spanish = None

        # parse the querystring parameters component
        parsed_qs = parse_qs(parsed_url.query)
        if 'pad' in parsed_qs:
            pad = int(parsed_qs['pad'][0])
        if 'alternate_english' in parsed_qs:
            alternate_english = urllib.unquote_plus(parsed_qs['alternate_english'][0])
        if 'alternate_spanish' in parsed_qs:
            alternate_spanish = urllib.unquote_plus(parsed_qs['alternate_spanish'][0])

        for key in self.headers:
            if key.lower() not in REMOVE_IN_HEADERS:
                headers[key] = self.headers[key]

        response = requests.get(url, headers=headers)

        self.send_response(response.status_code)

        for key in response.headers:
            if key.lower() not in REMOVE_OUT_HEADERS:
                if key.lower() == 'access-control-allow-origin':
                    response.headers[key] = '*'
                self.send_header(key, response.headers[key])

        self.end_headers()

        content = response.content.decode('utf8')

        # change relative m3u8 urls to absolute urls by looking at each line
        line_array = content.splitlines()
        new_line_array = []
        for line in line_array:
            if line.startswith('#'):
                # look for uri parameters within non-key "#" lines
                if KEY_TEXT not in line and URI_START_DELIMETER in line:
                    line_split = line.split(URI_START_DELIMETER)
                    url_split = line_split[1].split(URI_END_DELIMETER, 1)
                    absolute_url = urljoin(url, url_split[0])
                    if absolute_url.endswith(STREAM_EXTENSION) and not absolute_url.startswith(PROXY_URL):
                        absolute_url = PROXY_URL + absolute_url + '?' + parsed_url.query
                    new_line = line_split[0] + URI_START_DELIMETER + absolute_url + URI_END_DELIMETER + url_split[1]
                    new_line_array.append(new_line)
                else:
                    new_line_array.append(line)
                    if line == '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aac",LANGUAGE="en",NAME="English",AUTOSELECT=YES,DEFAULT=YES':
                        if alternate_english is not None:
                            new_line_array.append('#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aac",NAME="Alternate English",LANGUAGE="en",AUTOSELECT=YES,DEFAULT=NO,URI="' + PROXY_URL + alternate_english + '?' + parsed_url.query + '"')
                        if alternate_spanish is not None:
                            new_line_array.append('#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aac",NAME="Alternate Spanish",LANGUAGE="es",AUTOSELECT=YES,DEFAULT=NO,URI="' + PROXY_URL + alternate_spanish + '?' + parsed_url.query + '"')
            elif line != '':
                absolute_url = urljoin(url, line)
                if absolute_url.endswith(STREAM_EXTENSION) and not absolute_url.startswith(PROXY_URL):
                    absolute_url = PROXY_URL + absolute_url + '?' + parsed_url.query
                new_line_array.append(absolute_url)

        # pad the end of the stream by the requested number of segments
        last_item_index = len(new_line_array)-1
        if new_line_array[last_item_index] == ENDLIST_TEXT and int(pad) > 0:
            new_line_array.pop()
            last_item_index -= 1
            url_line = None
            extinf_line = None
            while extinf_line is None:
                if new_line_array[last_item_index].startswith('#EXTINF:5'):
                    extinf_line = new_line_array[last_item_index]
                    url_line = new_line_array[last_item_index+1]
                    break
                last_item_index -= 1
            for x in range(0, pad):
                new_line_array.append(extinf_line)
                new_line_array.append(url_line)
            new_line_array.append(ENDLIST_TEXT)

        content = "\n".join(new_line_array)

        # Output the new content
        self.wfile.write(content.encode('utf8'))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

server = ThreadedHTTPServer((HOST, PORT), RequestHandler)
server.allow_reuse_address = True
httpd_thread = threading.Thread(target=server.serve_forever)
httpd_thread.start()

xbmc.Monitor().waitForAbort()

server.shutdown()
server.server_close()
server.socket.close()
httpd_thread.join()
