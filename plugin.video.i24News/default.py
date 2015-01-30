# -*- coding: utf-8 -*-
# i24News Addon by t1m

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import cgi, gzip
from StringIO import StringIO

import pyamf
from pyamf import remoting

CONST = '84c401e577ddd24ca827eab0184302b8281e8b51'

USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
GENRE_NEWS  = "News"
UTF8          = 'utf-8'
BASE_URL      = 'http://www.i24news.tv'

addon         = xbmcaddon.Addon('plugin.video.i24News')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart        = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def deuni(a):
    a = a.replace('&amp;#039;',"'")
    a = a.replace('&amp','&')
    a = a.replace('&#039;',"'")
    a = a.replace('&quot;','"')
    return a

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


def getRequest(url):
              log("getRequest URL:"+str(url))
              headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8', 'Cookie':'hide_ce=true'} 
              req = urllib2.Request(url.encode(UTF8), None, headers)

              try:
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()
              except:
                 link1 = ""

              link1 = str(link1).replace('\n','')
              return(link1)


def getSources(replay_url):

          if replay_url == '/ar/tv-ar/revoir-ar':
             addLink("plugin://plugin.video.i24News/?url=#2552000981001&mode=PV",__language__(30000)+" "+__language__(30003),icon,fanart,__language__(30000)+" "+__language__(30003),GENRE_NEWS,"")
             getCats(replay_url)
          else:
            if replay_url == '/en/tv/replay':
               addDir(__language__(30002),'/fr/tv/revoir','GX',icon,fanart,__language__(30002),GENRE_NEWS,"",False)
               addDir(__language__(30003),'/ar/tv-ar/revoir-ar','GX',icon,fanart,__language__(30003),GENRE_NEWS,"",False)
               addLink("plugin://plugin.video.i24News/?url=#2552000984001&mode=PV",__language__(30000)+" "+__language__(30001),icon,fanart,__language__(30000)+" "+__language__(30001),GENRE_NEWS,"")
            else:
               addLink("plugin://plugin.video.i24News/?url=#2552024981001&mode=PV",__language__(30000)+" "+__language__(30002),icon,fanart,__language__(30000)+" "+__language__(30002),GENRE_NEWS,"")
            link=getRequest(BASE_URL+replay_url)
            match = re.compile('<li id=".+?href="(.+?)".+?>(.+?)<').findall(link)
            for pchoice, pname in match:
               if not ('</a>' in pname):
                addDir(deuni(pname),pchoice,'GC',icon,fanart,deuni(pname),GENRE_NEWS,"",False)


def getCats(Category_url):

              log("main page")
              link = getRequest(BASE_URL+Category_url)
              match = re.compile('<li class="results-item">.+?href="(.+?)".+?<img src="(.+?)".+?mosaic-view">(.+?)<.+?<span>(.+?)<.+?description">(.+?)<.+?</p>').findall(link)
              for pid, pimage, pname, pdate, pdesc in match:
                     pname = pname.strip()
                     pdesc  = pdate.strip()+'\n'+pdesc.strip()
                     pid1 = pid.split('/')
                     pid = pid1[len(pid1)-1]
                     caturl = "plugin://plugin.video.i24News/?url=#"+str(pid)+"&mode=PV"
                     try:
                        addLink(caturl.encode(UTF8),deuni(pname),pimage,fanart,deuni(pdesc),GENRE_NEWS,"")
                     except:
                        log("Problem adding directory")
              try:
                     url = re.compile('title="next page" href="(.+?)"').findall(link)[0]
                     addDir('[COLOR blue]%s[/COLOR]' % (__language__(30004)), url, 'GC', icon, fanart,(__language__(30004)), GENRE_NEWS,"",False)
              except:
                     return


def play_playlist(name, list):
        playlist = xbmc.PlayList(1)
        playlist.clear()
        item = 0
        for i in list:
            item += 1
            info = xbmcgui.ListItem('%s) %s' %(str(item),name))
            playlist.add(i, info)
        xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage,fanart,description,genre,date,showcontext=True,playlist=None,autoplay=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+mode
        dir_playable = False
        cm = []

        if mode != 'SR':
            u += "&name="+urllib.quote_plus(name)
            if (fanart is None) or fanart == '': fanart = addonfanart
            u += "&fanart="+urllib.quote_plus(fanart)
            dir_image = "DefaultFolder.png"
            dir_folder = True
        else:
            dir_image = "DefaultVideo.png"
            dir_folder = False
            dir_playable = True

        ok=True
        liz=xbmcgui.ListItem(name, iconImage=dir_image, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Year": date } )
        liz.setProperty( "Fanart_Image", fanart )

        if dir_playable == True:
         liz.setProperty('IsPlayable', 'true')
        if not playlist is None:
            playlist_name = name.split(') ')[1]
            cm.append(('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=PP&name=%s&playlist=%s)' %(sys.argv[0], playlist_name, urllib.quote_plus(str(playlist).replace(',','|')))))
        liz.addContextMenuItems(cm)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=dir_folder)

def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None, autoplay=False):
        return addDir(name,url,'SR',iconimage,fanart,description,genre,date,showcontext,playlist,autoplay)


def playVideo(video_url):
	video_player_key = "AQ~~,AAACL1AyZ1k~,hYvoCrzvEtv6DS-0RQ1DkpOvkcvXlQ-g"
	page_url = "http://www.i24news.tv/en/tv/replay/culture/3121368590001"
	video_player_id = "2551661482001"
	publisher_id = "2402232199001"

	video_url, video_content_id = video_url.split('#')
	swf_url = get_swf_url("myExperience",video_player_id,publisher_id,str(video_content_id))
	renditions = get_episode_info(video_player_key,str(video_content_id),page_url,video_player_id)
	finalurl = renditions['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']

# use 'IOSRenditions' in place of 'renditions' in below for .m3u8 list, note case of 'r' in renditions, using 'renditions' gives you rtmp links

	stored_size=stored_height = 0
	for item in sorted(renditions['programmedContent']['videoPlayer']['mediaDTO']['renditions'], key = lambda item:item['frameHeight'], reverse = False):
		stream_size = item['size']
		stream_height = item['frameHeight']
		if (int(stream_size) > stored_size):
			finalurl = item['defaultURL']
			stored_size = stream_size
			stored_height = stream_height

#this is a kludge because I can't get some rtmps to play, so use the IOS .m3u8 list if it exists (the ones with IOSRenditions don't play rtmp correctly)
#
#	if (stored_height == 720) and (addon.getSetting('vid_res') == "1") and ("&mp4:23/" in finalurl):
#		match = re.compile('&mp4:(.+?)\?').findall(finalurl)
#		for x in match:
#			finalurl = "http://brightcove04.brightcove.com/"+x
#	else:
	stored_size = 0
	for item in sorted(renditions['programmedContent']['videoPlayer']['mediaDTO']['IOSRenditions'], key = lambda item:item['frameHeight'], reverse = False):
			stream_size = item['size']
			if (int(stream_size) > stored_size):
				finalurl = item['defaultURL']
				stored_size = stream_size

	finalurl = finalurl.replace('.mp4?','.mp4&') # this needs work where the app, playpath, wierdqs split doesn't work right below

	if "rtmp:" in finalurl:
		app, playpath, wierdqs = finalurl.split("&", 2)
		qs = "?videoId=%s&lineUpId=&pubId=%s&playerId=%s&affiliateId=" % (video_content_id, publisher_id, video_player_id)
		scheme,netloc = app.split("://")
		netloc, app = netloc.split("/",1)
		app = app.rstrip("/") + qs
		log("APP:%s" %(app,))
		tcurl = "%s://%s:1935/%s" % (scheme, netloc, app)
		log("TCURL:%s" % (tcurl,))
		finalurl = "%s tcUrl=%s app=%s playpath=%s%s swfUrl=%s conn=B:0 conn=S:%s&%s" % (tcurl,tcurl, app, playpath, qs, swf_url, playpath, wierdqs)
		log("final rtmp: url =%s" % (finalurl,))
	else:
		finalurl = finalurl.replace('-vh.akamaihd','.brightcove.com.edgesuite')

	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))


def get_episode_info(video_player_key, video_content_id, video_url, video_player_id):

	envelope = build_amf_request(video_player_key, video_content_id, video_url, video_player_id)
	connection_url = "http://c.brightcove.com/services/messagebroker/amf?playerKey=" + video_player_key
	values = bytes(remoting.encode(envelope).read())
	header = {'Content-Type' : 'application/x-amf'}
	response = remoting.decode(getURL(connection_url, values, header, amf = True)).bodies[0][1].body
	log("Episode Info response: %s" % (response,))
	return response

def getURL(url, values = None, header = {}, amf = False, cookieinfo = False):
	try:
		if values is None:
			req = urllib2.Request(bytes(url))
		else:
			if amf == False:
				data = urllib.urlencode(values)
			elif amf == True:
				data = values
			req = urllib2.Request(bytes(url), data)
		header.update({'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0'})
		for key, value in header.iteritems():
			req.add_header(key, value)
		response = urllib2.urlopen(req)
		link = response.read()
		cookie = response.info()
		response.close()
	except urllib2.HTTPError, error:
		log("HTTP Error reason: %s" % (error,))
		return error.read()
	else:
		if cookieinfo is True:
			return link, cookie
		else:
			return link



class ViewerExperienceRequest(object):
	def __init__(self, URL, contentOverrides, experienceId, playerKey, TTLToken = ''):
		self.TTLToken = TTLToken
		self.URL = URL
		self.deliveryType = float(0)
		self.contentOverrides = contentOverrides
		self.experienceId = experienceId
		self.playerKey = playerKey

class ContentOverride(object):
	def __init__(self, contentId, contentType = 0, target = 'videoPlayer'):
		self.contentType = contentType
		self.contentId = contentId
		self.target = target
		self.contentIds = None
		self.contentRefId = None
		self.contentRefIds = None
		self.contentType = 0
		self.featureId = float(0)
		self.featuredRefId = None

def build_amf_request(video_player_key, video_content_id, video_url, video_player_id):
	pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')
	pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')
	content_override = ContentOverride(int(video_content_id))
	viewer_exp_req = ViewerExperienceRequest(video_url, [content_override], int(video_player_id), video_player_key)
	env = remoting.Envelope(amfVersion=3)
	env.bodies.append(
	(
		"/1",
		remoting.Request(
			target = "com.brightcove.experience.ExperienceRuntimeFacade.getDataForExperience",
			body = [CONST, viewer_exp_req],
			envelope = env
		)
	)
	)
	return env
 
def get_swf_url(flash_experience_id, player_id, publisher_id, video_id):
        conn = httplib.HTTPConnection('c.brightcove.com')
        qsdata = dict(width=640, height=480, flashID=flash_experience_id, 
                      bgcolor="#000000", playerID=player_id, publisherID=publisher_id,
                      isSlim='true', wmode='opaque', optimizedContentLoad='true', autoStart='', debuggerID='')
        qsdata['@videoPlayer'] = video_id
        log("SWFURL: %s" % (urllib.urlencode(qsdata),))
        conn.request("GET", "/services/viewer/federated_f9?&" + urllib.urlencode(qsdata))
        resp = conn.getresponse()
        location = resp.getheader('location')
        base = location.split("?",1)[0]
        location = base.replace("BrightcoveBootloader.swf", "federatedVideo/BrightcovePlayer.swf")
        return location


# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'movies')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
       parms[key] = demunge(parms[key])
except:
    parms = {}

p = parms.get

mode = p('mode',None)

if mode==  None:  getSources('/en/tv/replay')
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GC':  getCats(p('url'))
elif mode=='PV':  playVideo(p('url'))
elif mode=='GX':  getSources(p('url'))


xbmcplugin.endOfDirectory(int(sys.argv[1]))

sys.modules.clear()
