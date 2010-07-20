"""
 A plugin to get radio links from listenlive.eu
"""

import sys, os, os.path, xbmcaddon
import xbmc, xbmcgui, xbmcplugin
import urllib, re, time
from shutil import rmtree, copy
import traceback
from pprint import pprint

__plugin__ = "ListenLiveEU"
__version__ = '0.3.1'
__author__ = 'bootsy [bootsy82@gmail.com]'
__date__ = '19-07-2010'
__svn__ = 'http://xbmc-addons.googlecode.com/svn/addons/plugin.audio.ListenLiveEU/'

BASE_URL = 'http://www.listenlive.eu'
URL_INDEX = '/'.join( [BASE_URL, 'index.html'] )
URL_NEW = '/'.join( [BASE_URL, 'new.html'] )

DIR_HOME = os.getcwd().replace(';','')
FILE_INDEX_PAGE = os.path.join(DIR_HOME, 'index.html')
FILE_NEW_PAGE = os.path.join(DIR_HOME, 'new.html')

def log(msg):
	if type(msg) not in (str, unicode):
		xbmc.output("[%s]: %s" % (__plugin__, type(msg)))
		pprint (msg)
	else:
		xbmc.output("[%s]: %s" % (__plugin__, msg))

def errorOK(title="", msg=""):
	e = str( sys.exc_info()[ 1 ] )
	log(e)
	if not title:
		title = __plugin__
	if not msg:
		msg = "ERROR!"
	xbmcgui.Dialog().ok( title, msg, e )
	
dialogProgress = xbmcgui.DialogProgress()

#######################################################################################################################    
# get initial root category
#######################################################################################################################    
def getRootCats():
	log("> getRootCats()")
	items = ( (__language__(1010), "new"), (__language__(1020),"country"), (__language__(1030),"genre"), )

	for title, url in items:
		addDirectoryItem(title, url, 0)

	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	log("< getRootCats()")
	return True

#######################################################################################################################    
# Get category of by country or by genre
#######################################################################################################################    
def getCats(byCountry):
	log("> getCats() byCountry=%s" % byCountry)
	ok = False

	doc = getURL(URL_INDEX, FILE_INDEX_PAGE)
	if doc:
		log("getCats() parsing ...")
		try:
			# get section
			baseRE = '<p>Browse by $SECTION.*?</div>(.+?)</tr></tbody></table></div><br />'
			if byCountry:
				sectionRE = baseRE.replace('$SECTION','country')
			else:
				sectionRE = baseRE.replace('$SECTION','genre')
			section = re.search(sectionRE, doc, re.IGNORECASE + re.MULTILINE + re.DOTALL).group(1)

			# parse info from section
			p=re.compile('<a href="(.+?)".*?>(.+?)</a', re.IGNORECASE)
			matches = p.findall(section)
			for page, name in matches:
				url = "/".join([BASE_URL,page])
				addDirectoryItem(name,url,1)

			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
			ok = True
		except:
			errorOK("getCats()")

	log("< getCats() ok=%s" % ok)
	return ok


######################################################################################################
def getStreams(url):
	log("> getStreams()")
	ok = False

	#doc = open('/'.join( [DIR_HOME, 'top40.html'] ) ).read()				# frig for dev only
	doc = getURL(url)
	if doc:
		try:
			log("parsing doc ...")
			doc=doc.replace('<br />','')
			# get all table rows, one staion per row - with possible multiple streams
			stationsRE=re.compile('(<tr>.*?</tr>)', re.IGNORECASE + re.MULTILINE + re.DOTALL)

			# url, name, loc, stream(s), genre
			#stationRE=re.compile('<td><a href=".*?"><b>(.*?)</b>.*?<td>(.*?)</td>.*?alt=".*?".*?<td>(<a href=.*?</td>).*?(?:<td>(.*?)</td>|</tr>)', re.IGNORECASE + re.MULTILINE + re.DOTALL)
			stationRE=re.compile('<td.+?<a href=".*?"><b>(.*?)</b>.*?<td>(.*?)</td>.*?alt=".*?".*?<td>(<a href=.*?</td>).*?(?:<td>(.*?)</td>|</tr>)', re.IGNORECASE + re.MULTILINE + re.DOTALL)

			#streamsRE=re.compile('href="(.*?)">(.*?)<', re.IGNORECASE)
			streamsRE=re.compile('href="([^"]+)">(\d+ +[^"]+|\d+[.]\d+ +[^"]+)</a>', re.IGNORECASE)

			# get all stations
			stations = stationsRE.findall(doc)
			#pprint (stations)
			genreExists = False
			for station in stations:
				#print station

				# get station details
				stationInfo = re.search(stationRE, station, re.IGNORECASE + re.MULTILINE + re.DOTALL)
				if not stationInfo:
					log("stationInfo re not matched - ignore station")
					continue
				#print stationInfo.groups()

				# ensure we only use allowed stream type
				#type = stationInfo.group(3)
				#if type not in ('MP3','Windows Media'):							# add allowed type here
				#	log("ignored stream type: " + type)
				#	continue
				
				name = stationInfo.group(1)
				loc = stationInfo.group(2)
				streamsData = stationInfo.group(3)
				genre = stationInfo.group(4)

				# parse station streams
				streams = streamsRE.findall(streamsData)
				
				for stream in streams:
					streamURL = stream[0]
					streamRate = stream[1]
					if not streamRate.endswith('Kbps') or streamRate.endswith('kbps'):
						log("ignored stream rate: " + streamRate)
						continue
					# further filter stream playlist types
					#if streamURL.endswith('.m3u') or streamURL.endswith('.pls'):
						#if not streamURL.endswith('ogg.m3u') and not streamURL.endswith('aac.m3u'):
							# stream allowed, display it
					infolabels = {}
					label1 = "%s" % (name)
					
					if list_loc=='true':
						label1 += " | %s" % (loc)

					if genre:
						if list_genre=='true':
							label1 += " | %s" % (genre)
						infolabels["Genre"] = genre
						genreExists = True				# if any have genre then allow SORT_METHOD

					if list_rate=='true':
						label1 += " | %s" % (streamRate)
						
					infolabels["Title"] = label1
					streamRate2= streamRate.replace('Kbps', '')
					streamRate2= streamRate2.replace('kbps', '')
					#print 'rate2: ' + streamRate2 + ' - ' + 'min_rate: ' + min_rate
					if float(streamRate2) >= float(min_rate):
						#print 'show it!'
						addDirectoryItem(label1, streamURL, 2, infoLabels=infolabels, isFolder=False)

			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
			if genreExists:
				xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
			ok = True
		except:
			errorOK("getStreams()")
	log("< getStreams() ok=%s" % ok)
	return ok

######################################################################################################
# fetch webpage or open filename if exists
######################################################################################################
def getURL(url, fn=''):
	""" read a doc from a url and save to file (if required) """
	
	try:
		doc = ''
		# load local file if exists
		if fn and os.path.isfile(fn):
			doc = open(fn).read()
			if not doc:
				deleteFile(fn)			# empty file, remove it
				log("Empty file removed: " + fn)
				doc = ''
			else:
				log("Loaded existing file: " + fn)

		if not doc:
			safe_url = url.replace( " ", "%20" )
			log('Downloading from url=%s' % safe_url)
			sock = urllib.urlopen( safe_url )
			doc = sock.read()
			if fn:
				fp = open(fn, "w")
				fp.write(doc)
				fp.close()
				log("File saved to " + fn)
			sock.close()

		if doc:
			return unicode(doc, 'UTF-8')
		else:
			return ''
	except:
		errorOK("getURL()")
		return None

######################################################################################################
def get_params():
	""" extract params from argv[2] to make a dict (key=value) """
	paramDict = {}
	try:
		print "get_params() argv=", sys.argv
		if sys.argv[2]:
			paramPairs=sys.argv[2][1:].split( "&" )
			for paramsPair in paramPairs:
				paramSplits = paramsPair.split('=')
				if (len(paramSplits))==2:
					paramDict[paramSplits[0]] = paramSplits[1]
	except:
		errorOK()
	return paramDict

######################################################################################################
def addDirectoryItem(name, url, mode, label2='', infoType="Music", infoLabels = {}, isFolder=True):
	liz=xbmcgui.ListItem(name, label2)
	if not infoLabels:
		infoLabels = {"Title": name }
	
	liz.setInfo( infoType, infoLabels )
	#u = "%s?url=%s&mode=%s&name=%s" % (sys.argv[0], urllib.quote_plus(url), mode, urllib.quote_plus(name), )
	u = "%s?url=%s&mode=%s&name=%s" % (sys.argv[0], urllib.quote_plus(url), mode, urllib.quote_plus(name.encode('utf-8')), )
	log("%s" % u)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)

######################################################################################################
def playStream(url):
	try:
		log("> playStream() " + url)
		plyr = xbmc.Player()
		plyr.play(str(url))
		isPlaying = plyr.isPlaying()
		log("< playStream() isPlaying=%s" % isPlaying)
		return isPlaying
	except:
		errorOK("playStream()")
		return False

######################################################################################################
def deleteFile(fn):
	try:
		os.remove(fn)
		log("File deleted: " + fn)
	except: pass
		
#######################################################################################################################    
# BEGIN !
#######################################################################################################################
try:
	__settings__ = xbmcaddon.Addon(id='plugin.audio.ListenLiveEU')
	__language__ = __settings__.getLocalizedString
except:
	errorOK()

#######################################################################################################################    
# get settings
#######################################################################################################################

list_loc = __settings__.getSetting( "list_loc" )
list_genre = __settings__.getSetting( "list_genre" )
list_rate = __settings__.getSetting( "list_rate" )
min_rate = __settings__.getSetting( "min_rate" )

#######################################################################################################################
params=get_params()
url=urllib.unquote_plus(params.get("url", ""))
name=urllib.unquote_plus(params.get("name",""))
mode=int(params.get("mode","0"))
log("Mode: %s" % mode)
log("URL: %s" % url)
log("Name: %s" % name)

if not sys.argv[ 2 ] or not url:
	# new start - cleanup old files
	deleteFile(FILE_INDEX_PAGE)
	deleteFile(FILE_NEW_PAGE)

	ok = getRootCats()
elif url == "new":
	ok = getStreams(URL_NEW)
elif url == "country":
	ok = getCats(True)
elif url == "genre":
	ok = getCats(False)
elif mode==1:
	ok = getStreams(url)
elif mode==2:
	ok = playStream(url)
xbmcplugin.endOfDirectory(int(sys.argv[1]), ok)