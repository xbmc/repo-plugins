import urllib2
import json

def loadUrl (url):
	response = urllib2.urlopen(url)
	html = response.read()
	return html	

def loadJsonFromUrl (url):
	data = None
	try:
		response = urllib2.urlopen(url)
		data = json.load(response)
	except:
		pass
	return data
