'''
    OneDrive for Kodi
    Copyright (C) 2015 - Carlos Guzman

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

    Created on Mar 1, 2015
    @author: Carlos Guzman (cguZZman) carlosguzmang@hotmail.com
'''

import json
import BaseHTTPServer

class download(BaseHTTPServer.BaseHTTPRequestHandler):
    file_map = {}

    def do_HEAD(self):
        self.do_GET()
        return

    def do_GET(self):
        url = ''
        if self.path in self.file_map:
            url = self.file_map[self.path]
        self.send_response(303)
        self.send_header('Location', url)
        self.end_headers()
        return

    def do_POST(self):
        self.file_map[self.path] = self.headers.get('download-url')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': 'true', self.path : self.file_map[self.path]}));
        self.wfile.close()
        