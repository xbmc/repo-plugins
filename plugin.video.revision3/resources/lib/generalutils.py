# -*- coding: utf-8 -*-
'''
    plugin.video.revision3
    Copyright (C) 2017 enen92,stacked
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

import urllib2

useragent = 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'


def get_page(url, gzip = False):
	data = {'content': None, 'error': None}
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', useragent)
		content = urllib2.urlopen(req)
		if gzip:
			try:
				if content.info()['Content-Encoding'] == 'gzip':
					import gzip, StringIO
					gzip_filehandle = gzip.GzipFile(fileobj=StringIO.StringIO(content.read()))
					html = gzip_filehandle.read()
				else:
					html = content.read()
			except:
				html = content.read()
		else:
			html = content.read()
		content.close()
		try:
			data['content'] = html.decode('utf-8')
			return data
		except:
			data['content'] = html
			return data
	except Exception, e:
		data['error'] = str(e)
		return data