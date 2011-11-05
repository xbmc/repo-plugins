'''
   Parsedom for XBMC plugins
   Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

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

import sys, urllib2, re, inspect

class CommonFunctions:
	
	def __init__(self):
		self.plugin = "CommonFunctions-0.8"
		self.USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"


		if sys.modules[ "__main__" ].xbmc:
			self.xbmc = sys.modules["__main__"].xbmc
		else:
			import xbmc
			self.xbmc = xbmc

		if sys.modules[ "__main__" ].dbglevel:
			self.dbglevel = sys.modules[ "__main__" ].dbglevel
		else:
			self.dbglevel = 3

		if sys.modules[ "__main__" ].dbg:
			self.dbg = sys.modules[ "__main__" ].dbg
		else:
			self.dbg = True

	def stripTags(self, html):
		sub_start = html.find("<")
		sub_end = html.find(">")
		while sub_start < sub_end and sub_start > -1:
			html = html.replace(html[sub_start:sub_end + 1], "").strip()
			sub_start = html.find("<")
			sub_end = html.find(">")

		return html

	def getDOMContent(self, html, name, match):
		self.log("match: " + match, 2)
		start = html.find(match)
		endstr = "</" + name + ">"
		end = html.find(endstr, start)

		pos = html.find("<" + name, start + 1 )
		self.log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end), 8)

		while pos < end and pos != -1:
			tend = html.find(endstr, end + len(endstr))
			if tend != -1:
				end = tend
				pos = html.find("<" + name, pos + 1)
			self.log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos), 8)

		self.log("start: %s, end: %s" % ( start + len(match), end), 2)
		if start == -1 and end == -1:
			html = ""
		elif start > -1 and end > -1:
			html = html[start + len(match):end]
		#elif end > -1:
		#	html = html[:end]
		#elif start > -1:
		#	html = html[start + len(match):]

		self.log("done html length: " + str(len(html)) + ", content: " + html, 2)
		return html

	def getDOMAttributes(self, lst):
		self.log("", 2)
		ret = []
		for tmp in lst:
			if tmp.find('="') > -1:
				tmp = tmp[:tmp.find('="')]

			if tmp.find('=\'') > -1:
				tmp = tmp[:tmp.find('=\'')]

			cont_char = tmp[0]
			tmp = tmp[1:]
			if tmp.rfind(cont_char) > -1:
				tmp = tmp[:tmp.rfind(cont_char)]
			tmp = tmp.strip()
			ret.append(tmp)

		self.log("Done: " + repr(ret), 2)
		return ret

	def parseDOM(self, html, name = "", attrs = {}, ret = False):
		# html <- text to scan.
		# name <- Element name
		# attrs <- { "id": "my-div", "class": "oneclass.*anotherclass", "attribute": "a random tag" }
		# ret <- Return content of element
		# Default return <- Returns a list with the content
		self.log("start: " + repr(name) + " - " + repr(attrs) + " - " + repr(ret) + " - " + str(type(html)), 1)

		if type(html) != type([]):
			html = [html]
		
		if not name.strip():
			self.log("Missing tag name")
			return ""

		ret_lst = []

		# Find all elements with the tag
			
		i = 0
		for item in html:
			item = item.replace("\n", "")
			lst = []

			for key in attrs:
				scripts = [ '(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"][^>]*?>))', # Hit often.
					    '(<' + name + ' (?:' + key + '=[\'"]' + attrs[key] + '[\'"])[^>]*?>)', # Hit twice
					    '(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"])[^>]*?>)'] # 

				lst2 = []
				for script in scripts:
					if len(lst2) == 0:
						#self.log("scanning " + str(i) + " " + str(len(lst)) + " Running :" + script, 2)
						lst2 = re.compile(script).findall(item)
						i += 1
				if len(lst2) > 0:
					if len(lst) == 0:
						lst = lst2;
						lst2 = []
					else:
						test = range(len(lst))
						test.reverse()
						for i in test: # Delete anything missing from the next list.
							if not lst[i] in lst2:
								self.log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]), 1)
								del(lst[i])
	
			if len(lst) == 0 and attrs == {}:
				self.log("no list found, making one on just the element name", 1)
				lst = re.compile('(<' + name + '[^>]*?>)').findall(item)
	
			if ret != False:
				self.log("Getting attribute %s content for %s matches " % ( ret, len(lst) ), 2)
				lst2 = []
				for match in lst:
					tmp_list = re.compile('<' + name + '.*?' + ret + '=([\'"][^>]*?)>').findall(match)
					lst2 += self.getDOMAttributes(tmp_list)
					self.log(lst, 3)
					self.log(match, 3)
					self.log(lst2, 3)
				lst = lst2
			elif name != "img":
				self.log("Getting element content for %s matches " % len(lst), 2)
				lst2 = []
				for match in lst:
					temp = self.getDOMContent(item, name, match).strip()
					item = item[item.find(match + temp) + len(match + temp):]
					lst2.append(temp)
					self.log(lst, 3)
					self.log(match, 3)
					self.log(lst2, 3)
				lst = lst2
			ret_lst += lst

		self.log("Done", 1)
		return ret_lst

	def _fetchPage(self, params = {}):
		get = params.get
		link = get("link")
		ret_obj = {}
		self.log("called for : " + repr(params))

		if not link or int(get("error", "0")) > 2 :
			self.log("giving up")
			ret_obj["status"] = 500
			return ret_obj

		request = urllib2.Request(link)
		request.add_header('User-Agent', self.USERAGENT)

		try:
			self.log("connecting to server...", 1)

			con = urllib2.urlopen(request)
			
			ret_obj["content"] = con.read()
			ret_obj["new_url"] = con.geturl()
			ret_obj["header"] = str(con.info())
			con.close()

			self.log("Done")
			ret_obj["status"] = 200
			return ret_obj
		
		except urllib2.HTTPError, e:
			err = str(e)
			self.log("HTTPError : " + err)
			self.log("HTTPError - Headers: " + str(e.headers) + " - Content: " + e.fp.read())
			
			params["error"] = str(int(get("error", "0")) + 1)
			ret = self._fetchPage(params)

			if not ret.has_key("content") and e.fp:
				ret["content"] = e.fp.read()
				return ret

			ret_obj["status"] = 500
			return ret_obj
	
	def log(self, description, level = 0):
		if self.dbg and self.dbglevel > level:
			# Funny stuff..
			# [1][3] needed for calls from scrapeShow
			if isinstance(description, str):
				self.xbmc.log("[%s] %s : '%s'" % (self.plugin, inspect.stack()[1][3], description.encode("utf8", "ignore")), self.xbmc.LOGNOTICE)
			else:
				self.xbmc.log("[%s] %s : '%s'" % (self.plugin, inspect.stack()[1][3], description), self.xbmc.LOGNOTICE)
