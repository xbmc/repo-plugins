# coding: utf-8
#!/usr/bin/env python
import urllib2, re, os, xbmcgui, xbmc
from BeautifulSoup import BeautifulSoup
from datetime import datetime
import simplejson as json

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

def fetchPage(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', user_agent)
	response = urllib2.urlopen(req)
	html = response.read()
	response.close()
	return html

def getRootCategories():
	categories = []
	html = fetchPage("http://www.visir.is/section/MEDIA")
	soup = BeautifulSoup(html)
	ul = soup.find("ul", attrs={"id": "filmCatList"})
	for li in ul.findAll("li"):
		if (li['class'].find('undir') == -1):
			categories.append({"name":li.span.contents[0].encode('utf-8'), "id":li['aevar']})
	return categories

def getSubCategories(parent):
	categories = []
	html = fetchPage("http://www.visir.is/section/MEDIA")
	soup = BeautifulSoup(html)
	ul = soup.find("ul", attrs={"id": "filmCatList"})
	for li in ul.findAll("li"):
		if (li['class'].find('childof'+parent) > -1):
			type = ""
			if li.has_key('sourcetype'):
				type = li['sourcetype']
			categories.append({"name":li.span.contents[0].encode('utf-8'), "id": parent, "subid":li['aevar'], "type":type})
	return categories

def getVideos(category):
	videos = []
	
	cat = category.split(',')[0]
	subcat = category.split(',')[1]
	type = category.split(',')[2]

	html = fetchPage("http://www.visir.is/section/MEDIA01&template=mlist&pageNo=1&kat=" + cat +"&subkat=" + subcat + "&type=" + type)
	jsonData = json.JSONDecoder('latin1').decode(html)
	for video in jsonData['items']:
		fileid = video["url"].split('=')[-1].replace('CLP','').replace('SRC','').replace('VTV','')
		videos.append({"name":video["text"].encode('utf-8'), "fileid":fileid, "thumbnail":video["image"]})

	return videos