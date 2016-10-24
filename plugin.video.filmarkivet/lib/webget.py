# -*- coding: utf-8 -*-

'''
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

import os
import urllib
import hashlib
import datetime
import urllib2


class GetException(Exception):
	pass

class WebGet(object):
	API_URL = "http://www.filmarkivet.se"

	def __init__(self, cache_path):
		self.cache_path = cache_path

	def getURL(self, url='/'):
		print 'getURL:', url
		return self.__http_request(url)

	def __http_request(self, url, params=None, cache_minutes = 120):
		try:
			if not url.startswith('http://'):
				url = self.API_URL + url
			if params:
				url += '?' + urllib.urlencode(params, doseq=True)
			if self.cache_path:
				cache_path = os.path.join(self.cache_path, hashlib.md5(url).hexdigest() + '.cache')
				cache_until = datetime.datetime.now() - datetime.timedelta(minutes=cache_minutes)
				if not os.path.exists(cache_path) or datetime.datetime.fromtimestamp(os.path.getmtime(cache_path)) < cache_until:
					return self.__download_url(url, cache_path)
				else:
					with open(cache_path) as f:
						return f.read()
			else:
				return self.__download_url(url, None)
		except Exception as ex:
			raise GetException(ex)

	def __download_url(self, url, destination):
		u = urllib2.urlopen(url, timeout=30)
		data = u.read()
		u.close()

		if destination:
			try:
				with open(destination, 'w') as dest:
					dest.write(data)
			except:
				print 'Filmarkivet failed storing to cache.'

		return data
