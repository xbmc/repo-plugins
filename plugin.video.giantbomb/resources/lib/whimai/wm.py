# WhiMai v1.0.0 - A Python interface for Whiskey Media sites
# Copyright (C) 2010 Anders Bugge
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

# Contact Info
# E-Mail: whimais@gmail.com

# Thanks To
# http://www.whiskeymedia.com/
# http://www.giantbomb.com/
# http://www.comicvine.com/

import urllib
import simplejson as json

url_list = "http://api.%(site)s/%(name)s/?api_key=%(key)s&limit=%(lim)s&offset=%(off)s&%(extra)s&format=json"
url_detail = "http://api.%(site)s/%(name)s/%(id)s/?api_key=%(key)s&%(extra)s&format=json"

class E:
    def __init__(self,name):
        self.e = name
        
    def as_e(self,dct):
        if self.e in dct:
            return dct[self.e]
        return dct
    
class Parser:
	status_code = ""
	
	def parseData(self):
		try:
			f = urllib.urlopen( self.url )
			self.data = f.read()
			status_code = json.loads(self.data, object_hook=E('status_code').as_e)
			
		except:
			print "I/O error"
			return False
		
		else:
			if int(status_code) != 1:
				error = str(json.loads(self.data, object_hook=E('error').as_e))
				print "API Error: " + str(status_code) + ":" + error
				return False
			
			self.results = json.loads(self.data, object_hook=E('results').as_e)
			return True 

class DetailBase(Parser):
    key = ""
    name = ""
    site = ""
    extra = ""
    
    def __init__(self, name, site, key):
        self.name = name
        self.site = site
        self.key = key
        
    def update(self, id):
        self.url = url_detail%{'site': self.site, 'name': self.name, 'id': id, 'key': self.key, 'extra': self.extra}
        return self.parseData()

class ListBase(Parser):
    key = ""
    name = ""
    site = ""
    extra = ""
    
    def __init__(self, name, site, key):
        self.name = name
        self.site = site
        self.key = key
        
    def update(self, off, lim=25):
        self.url = url_list%{'site': self.site, 'name': self.name, 'lim': lim, 'off': off, 'key': self.key, 'extra': self.extra}
        return self.parseData()
    
    def getSize(self):
        return len(self.results)
    
    def getTotal(self):
        return json.loads(self.data, object_hook=E('number_of_total_results').as_e)
